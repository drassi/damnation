import os
import re
import sys
import json
import redis
import string
import random
import subprocess
import transaction

from sqlalchemy import engine_from_config
from pyramid.paster import get_appsettings, setup_logging

from ..models import DBSession, Base, Asset
from ..config import Config

REDIS = redis.Redis()

def get_abspath(asset):
    return os.path.join(Config.ASSET_ROOT, asset.path)

def load_asset(original_abspath):

    # get md5 and make sure we don't import a duplicate
    md5 = subprocess.check_output(['md5sum', original_abspath]).split(' ', 1)[0]
    if DBSession.query(Asset).filter(Asset.md5==md5).first():
        print 'skipping %s, file already imported with md5 %s' % (original_abspath, md5)
        return None

    # ffprobe the file to get dimensions and length and to ensure we can read it later
    try:
        ffprobe = subprocess.check_output(['ffprobe', '-show_streams', original_abspath], stderr=open('/dev/null', 'w'))
    except:
        print 'skipping %s, unable to ffprobe' % original_abspath
        return None
    durations = [int(d) for d in re.findall('^duration=(\d+)\.\d+\s*$', ffprobe, re.MULTILINE)]
    widths = [int(d) for d in re.findall('^width=(\d+)\s*$', ffprobe, re.MULTILINE)]
    heighths = [int(d) for d in re.findall('^height=(\d+)\s*$', ffprobe, re.MULTILINE)]
    if not durations or not widths or not heighths:
        print 'skipping %s, unable to get duration, width, height from ffprobe' % original_abspath
    duration, width, height = max(durations), max(widths), max(heighths)

    # copy the asset from it's original location into the asset store directory
    import_dir = os.path.join(md5[0:2], md5[2:4])
    import_absdir = os.path.join(Config.ASSET_ROOT, import_dir)
    if not os.path.isdir(import_absdir):
        os.makedirs(import_absdir)
    original_basename = os.path.basename(original_abspath)
    import_path = os.path.join(import_dir, original_basename)
    import_abspath = os.path.join(import_absdir, original_basename)
    subprocess.check_call(['cp', original_abspath, import_abspath])

    # persist asset metadata to the db
    size = os.path.getsize(import_abspath)
    asset = Asset('video', import_path, md5, size, duration, width, height, original_basename, original_abspath)
    print 'imported %s to %s size=%d' % (original_abspath, import_abspath, size)
    DBSession.add(asset)
    DBSession.flush()

    return asset

def load_assets(asset_root):
    assets = []
    for dirpath, dirnames, filenames in os.walk(asset_root):
        for filename in filenames:
            abspath = os.path.abspath(os.path.join(dirpath, filename))
            assets.append(load_asset(abspath))
    return filter(lambda x: x is not None, assets)

def rand4():
    return ''.join(random.choice(string.lowercase + string.digits) for i in xrange(4))

def queue_transcodes_and_screenshots(assets):
    [REDIS.sadd('resque:queues', q) for q in ['transcode', 'screenshot', 'thumbnail', 'youtube']]
    for asset in assets:
        inpath = asset.path
        infile = os.path.join(Config.ASSET_ROOT, inpath)

        flv_derivative_type = 'transcode.360.flv'
        flv_outpath = '%s.%s.%s' % (inpath, rand4(), flv_derivative_type)
        flv_outfile = os.path.join(Config.ASSET_ROOT, flv_outpath)
        flv_cmd = "ffmpeg -i %s -f flv -vf 'scale=-1:360' -r 15 -b 700 -g 10 -acodec libmp3lame -ar 22050 -ab 48000 -ac 1 -y %s" % (infile, flv_outfile)
        flvtool_cmd = 'flvtool2 -U %s' % flv_outfile
        flv_cmds = [flv_cmd, flvtool_cmd]

        num_screenshots = 14
        screenshot_derivative_type = 'screenshot.180.gif'
        screenshot_ffmpeg_filedirective = 'screenshot.180.%%02d.%d.png' % num_screenshots
        screenshot_outprefix = '%s.%s' % (inpath, rand4())
        screenshot_png_outfiles = os.path.join(Config.ASSET_ROOT, '%s.%s' % (screenshot_outprefix, screenshot_ffmpeg_filedirective))
        screenshot_rate = 1.0 * num_screenshots / asset.duration
        screenshot_pngs = 'screenshot.180.*.%d.png' % num_screenshots
        screenshot_pngs_abs = os.path.join(Config.ASSET_ROOT, '%s.%s' % (screenshot_outprefix, screenshot_pngs))
        screenshot_gifs = 'screenshot.180.*.%d.gif' % num_screenshots
        screenshot_gifs_abs = os.path.join(Config.ASSET_ROOT, '%s.%s' % (screenshot_outprefix, screenshot_gifs))
        screenshot_outfile = 'screenshot.180.%d.gif' % num_screenshots
        screenshot_outpath = '%s.%s' % (screenshot_outprefix, screenshot_outfile)
        screenshot_outfile_abs = os.path.join(Config.ASSET_ROOT, screenshot_outpath)
        screenshot_cmd = "ffmpeg -i %s -s 240x180 -r %.6f -vcodec png %s" % (infile, screenshot_rate, screenshot_png_outfiles)
        mogrify_cmd = 'mogrify -format gif %s' % screenshot_pngs_abs
        gifsicle_cmd = 'gifsicle --delay=50 --loop --colors 256 %s > %s' % (screenshot_gifs_abs, screenshot_outfile_abs)
        rm_cmd = 'rm %s %s' % (screenshot_pngs_abs, screenshot_gifs_abs)
        screenshot_cmds = [screenshot_cmd, mogrify_cmd, gifsicle_cmd, rm_cmd]

        thumbnail_derivative_type = 'thumbnail.180.png'
        thumbnail_outpath = '%s.%s.%s' % (inpath, rand4(), thumbnail_derivative_type)
        thumbnail_outfile = os.path.join(Config.ASSET_ROOT, thumbnail_outpath)
        thumbnail_location_secs = asset.duration / 4
        thumbnail_cmd = "ffmpeg -ss %d -i %s -t 1 -s 240x180 -vframes 1 -vcodec png %s" % (thumbnail_location_secs, infile, thumbnail_outfile)
        thumbnail_cmds = [thumbnail_cmd]

        REDIS.rpush('resque:queue:transcode',
                    json.dumps({'class': 'TranscodeAsset', 'args': [asset.id, flv_derivative_type, flv_cmds, flv_outpath]}))
        REDIS.rpush('resque:queue:screenshot',
                    json.dumps({'class': 'ScreenshotAsset', 'args': [asset.id, screenshot_derivative_type, screenshot_cmds, screenshot_outpath]}))
        REDIS.rpush('resque:queue:thumbnail',
                    json.dumps({'class': 'ThumbnailAsset', 'args': [asset.id, thumbnail_derivative_type, thumbnail_cmds, thumbnail_outpath]}))

def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> <asset_basepath>\n'
          '(example: "%s development.ini /path/to/asset/dir")' % (cmd, cmd)) 
    sys.exit(1)

def main(argv=sys.argv):
    if len(argv) != 3:
        usage(argv)
    config_uri = argv[1]
    asset_path = argv[2]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    print 'importing assets from %s..' % asset_path
    with transaction.manager:
        new_assets = load_assets(asset_path)
        print 'done importing %d assets, queueing transcoding..' % len(new_assets)
        queue_transcodes_and_screenshots(new_assets)
    print 'done!'
