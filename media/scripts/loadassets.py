import os
import re
import sys
import json
import redis
import string
import random
import subprocess
import transaction
from datetime import datetime

from sqlalchemy import engine_from_config
from pyramid.paster import get_appsettings, setup_logging

from ..models import DBSession, Base, Asset, Collection
from ..config import Config

REDIS = redis.Redis()

def get_abspath(asset):
    return os.path.join(Config.ASSET_ROOT, asset.path)

def load_asset(original_abspath, collection_id, now):

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
        return None
    duration, width, height = max(durations), max(widths), max(heighths)

    if duration == 0:
        print 'skipping %s, duration is zero' % original_abspath
        return None

    # copy the asset from it's original location into the asset store directory
    import_dir = os.path.join(md5[0:2], md5[2:4])
    import_absdir = os.path.join(Config.ASSET_ROOT, import_dir)
    if not os.path.isdir(import_absdir):
        os.makedirs(import_absdir)
    original_basename = os.path.basename(original_abspath)
    _, extension = os.path.splitext(original_basename)
    new_filename = md5 + extension.lower()
    import_path = os.path.join(import_dir, new_filename)
    import_abspath = os.path.join(import_absdir, new_filename)
    subprocess.check_call(['ln', '-s', original_abspath, import_abspath])

    # persist asset metadata to the db
    size = os.path.getsize(import_abspath)
    collection = DBSession.query(Collection).get(collection_id)
    asset = Asset(rand(6), 'video', import_path, md5, size, duration, width, height, unicode(original_basename), unicode(original_abspath), collection)
    asset.imported = now
    print 'imported %s to %s size=%d' % (original_abspath, import_abspath, size)
    DBSession.add(asset)
    DBSession.flush()

    return asset.id

def load_assets(asset_root, collection_id, now):
    [REDIS.sadd('resque:queues', q) for q in ['transcode', 'screenshot', 'thumbnail', 'youtube']]
    asset_ids = []
    for dirpath, dirnames, filenames in os.walk(asset_root):
        for filename in filenames:
            abspath = os.path.abspath(os.path.join(dirpath, filename))
            with transaction.manager:
                asset_id = load_asset(abspath, collection_id, now)
            if asset_id is not None:
                queue_transcode_and_screenshot(asset_id)
                asset_ids.append(asset_id)
    return asset_ids

def rand(n):
    return ''.join(random.choice(string.lowercase + string.digits) for i in xrange(n))

def queue_transcode_and_screenshot(asset_id):

    asset = DBSession.query(Asset).get(asset_id)

    inpath = asset.path
    infile = os.path.join(Config.ASSET_ROOT, inpath)

    mp4_derivative_type = 'transcode.360.mp4'
    mp4_outpath = '%s.%s.%s' % (inpath, rand(4), mp4_derivative_type)
    mp4_outfile = os.path.join(Config.ASSET_ROOT, mp4_outpath)
    mp4_tmpfile = mp4_outfile + '.tmp'
    mp4_cmd = "avconv -i %s -f mp4 -vf 'scale=-1:360' -r 15 -vcodec libx264 -b 512k -g 10 -acodec libmp3lame -ar 22050 -ab 48000 -ac 1 -y %s" % (infile, mp4_tmpfile)
    faststart_cmd = 'qt-faststart %s %s' % (mp4_tmpfile, mp4_outfile)
    rm_tmp_cmd = 'rm %s' % mp4_tmpfile
    mp4_cmds = [mp4_cmd, faststart_cmd, rm_tmp_cmd]

    num_screenshots = 14
    screenshot_derivative_type = 'screenshot.180.gif'
    screenshot_ffmpeg_filedirective = 'screenshot.180.%%02d.%d.png' % num_screenshots
    screenshot_outprefix = '%s.%s' % (inpath, rand(4))
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
    thumbnail_outpath = '%s.%s.%s' % (inpath, rand(4), thumbnail_derivative_type)
    thumbnail_outfile = os.path.join(Config.ASSET_ROOT, thumbnail_outpath)
    thumbnail_location_secs = asset.duration / 4
    thumbnail_cmd = "avconv -ss %d -i %s -t 1 -s 240x180 -vframes 1 -vcodec png -loglevel fatal %s" % (thumbnail_location_secs, infile, thumbnail_outfile)
    thumbnail_cmds = [thumbnail_cmd]

    REDIS.rpush('resque:queue:transcode',
                json.dumps({'class': 'TranscodeAsset', 'args': [asset.id, mp4_derivative_type, mp4_cmds, mp4_outpath]}))
    REDIS.rpush('resque:queue:screenshot',
                json.dumps({'class': 'ScreenshotAsset', 'args': [asset.id, screenshot_derivative_type, screenshot_cmds, screenshot_outpath]}))
    REDIS.rpush('resque:queue:thumbnail',
                json.dumps({'class': 'ThumbnailAsset', 'args': [asset.id, thumbnail_derivative_type, thumbnail_cmds, thumbnail_outpath]}))

def create_collection(import_name):
    collection_id = rand(6)
    with transaction.manager:
        collection = Collection(collection_id, import_name, '')
        DBSession.add(collection)
    return collection_id

def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> <asset_basepath> <import_name>\n'
          '(example: "%s development.ini /path/to/asset/dir \'brief title for import collection\'")' % (cmd, cmd)) 
    sys.exit(1)

def main(argv=sys.argv):
    if len(argv) != 4:
        usage(argv)
    config_uri = argv[1]
    asset_path = argv[2]
    import_name = argv[3]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    print 'importing assets from %s..' % asset_path
    collection_id = create_collection(import_name)
    new_asset_ids = load_assets(asset_path, collection_id, datetime.utcnow())
    print 'done importing %d assets' % len(new_asset_ids)
