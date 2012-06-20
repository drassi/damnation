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

from ..models import DBSession, Base, Asset, Collection, User, AssetLog, CollectionLog, ImportLog
from ..config import Config

REDIS = redis.Redis()

def get_abspath(asset):
    return os.path.join(Config.ASSET_ROOT, asset.path)

def log(logline, import_log):
    print logline
    import_log.log += logline + '\n'
    DBSession.add(import_log)

def load_asset(original_abspath, collection_id, import_log_id, now):

    import_log = DBSession.query(ImportLog).get(import_log_id)

    # get md5 and make sure we don't import a duplicate
    md5 = subprocess.check_output(['md5sum', original_abspath]).split(' ', 1)[0]
    dupe = DBSession.query(Asset).filter(Asset.md5==md5).first()
    if dupe:
        log('IMPORT : DUPE %s : %s' % (dupe.id, original_abspath), import_log)
        return None

    # ffprobe the file to get dimensions and length and to ensure we can read it later
    try:
        ffprobe = subprocess.check_output(['ffprobe', '-show_streams', original_abspath], stderr=open('/dev/null', 'w'))
    except:
        log('SKIP : FFPROBE FAIL : %s' % original_abspath, import_log)
        return None
    durations = [int(d) for d in re.findall('^duration=(\d+)\.\d+\s*$', ffprobe, re.MULTILINE)]
    widths = [int(d) for d in re.findall('^width=(\d+)\s*$', ffprobe, re.MULTILINE)]
    heighths = [int(d) for d in re.findall('^height=(\d+)\s*$', ffprobe, re.MULTILINE)]
    if not durations or not widths or not heighths:
        log('SKIP : FFPROBE MISSING DURATION or W or H : %s' % original_abspath, import_log)
        return None
    duration, width, height = max(durations), max(widths), max(heighths)

    if duration == 0:
        log('SKIP : FFPROBE DURATION ZERO : %s' % original_abspath, import_log)
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
    asset = Asset(rand(6), 'video', import_path, md5, size, duration, width, height, unicode(original_basename), '', unicode(original_abspath), collection, import_log)
    asset.imported = now
    log('IMPORT : OK %s : %s' % (asset.id, original_abspath), import_log)
    DBSession.add(asset)
    system = DBSession.query(User).get('000000')
    DBSession.add(AssetLog(system, asset, 'create', {}, new_collection=collection))

    return asset.id

def load_assets(asset_root, collection_id, import_log_id, now):
    [REDIS.sadd('resque:queues', q) for q in ['transcode', 'screenshot', 'thumbnail', 'youtube']]
    asset_ids = []
    for dirpath, dirnames, filenames in os.walk(asset_root):
        for filename in filenames:
            abspath = os.path.abspath(os.path.join(dirpath, filename))
            with transaction.manager:
                asset_id = load_asset(abspath, collection_id, import_log_id, now)
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
    ext = os.path.splitext(inpath)[1]

    duration = asset.duration
    size = asset.size
    bitrate = (size * 8) / (duration * 1024)
    transcode_bitrate = min(bitrate, 512)

    height = asset.height
    transcode_height = min(height, 480)

    transcode_arg_list = []
    mp4_derivative_type = 'transcode.480.mp4'
    chunk_size_secs = 3600
    num_parts = 1 + duration / chunk_size_secs
    for part in range(num_parts):
        mp4_outpath = '%s.%s.transcode.480.part%03d.mp4' % (inpath, rand(4), part)
        mp4_outfile = os.path.join(Config.ASSET_ROOT, mp4_outpath)
        mp4_tmpfile = mp4_outfile + '.tmp'
        screenshot_params = '-ss %d -t %d' % (part * chunk_size_secs, chunk_size_secs) if num_parts > 1 else ''
        mp4_cmd = "avconv -i %s %s -vcodec libx264 -vprofile high -preset medium -b:v %dk -r 30 -vf scale=-1:%d,yadif -acodec libvo_aacenc -b:a 64k -ar 44100 -ac 2 -f mp4 -y %s" % (infile, screenshot_params, transcode_bitrate, transcode_height, mp4_tmpfile)
        faststart_cmd = 'qt-faststart %s %s' % (mp4_tmpfile, mp4_outfile)
        rm_tmp_cmd = 'rm %s' % mp4_tmpfile
        cmds = [mp4_cmd, faststart_cmd, rm_tmp_cmd]
        transcode_arg_list.append([cmds, mp4_outpath, part])
        part += 1

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
    gifsicle_cmd = 'gifsicle --delay=50 --loop --colors 256 -o %s %s' % (screenshot_outfile_abs, screenshot_gifs_abs)
    rm_cmd = 'rm %s %s' % (screenshot_pngs_abs, screenshot_gifs_abs)
    screenshot_cmds = [screenshot_cmd, mogrify_cmd, gifsicle_cmd, rm_cmd]

    thumbnail_derivative_type = 'thumbnail.180.png'
    thumbnail_outpath = '%s.%s.%s' % (inpath, rand(4), thumbnail_derivative_type)
    thumbnail_outfile = os.path.join(Config.ASSET_ROOT, thumbnail_outpath)
    thumbnail_location_secs = asset.duration / 10
    thumbnail_cmd = "avconv -i %s -ss %d -t 1 -s 240x180 -vframes 1 -vcodec png %s" % (infile, thumbnail_location_secs, thumbnail_outfile)
    ls_cmd = 'ls %s' % thumbnail_outfile
    thumbnail_cmds = [thumbnail_cmd, ls_cmd]

    for cmds, outpath, part in transcode_arg_list:
        REDIS.rpush('resque:queue:transcode',
                    json.dumps({'class': 'TranscodeAsset', 'args': [asset.id, mp4_derivative_type, cmds, outpath, part]}))
    REDIS.rpush('resque:queue:screenshot',
                json.dumps({'class': 'ScreenshotAsset', 'args': [asset.id, screenshot_derivative_type, screenshot_cmds, screenshot_outpath, 0]}))
    REDIS.rpush('resque:queue:thumbnail',
                json.dumps({'class': 'ThumbnailAsset', 'args': [asset.id, thumbnail_derivative_type, thumbnail_cmds, thumbnail_outpath, 0]}))

def create_collection(import_name, asset_path):
    collection_id = rand(6)
    import_log_id = rand(6)
    with transaction.manager:
        collection = Collection(collection_id, import_name, u'')
        DBSession.add(collection)
        system = DBSession.query(User).get('000000')
        DBSession.add(ImportLog(import_log_id, asset_path, u''))
        DBSession.add(CollectionLog(system, None, collection, 'create', {}))
    return collection_id, import_log_id

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
    collection_id, import_log_id = create_collection(import_name, asset_path)
    new_asset_ids = load_assets(asset_path, collection_id, import_log_id, datetime.utcnow())
    print 'done importing %d assets' % len(new_asset_ids)
