import os
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

ASSET_ROOT = '/media/dam'
REDIS = redis.Redis()

def get_abspath(asset):
    return os.path.join(ASSET_ROOT, asset.path)

def load_asset(original_abspath):

    # get md5 and make sure we don't import a duplicate
    md5 = subprocess.check_output(['md5sum', original_abspath]).split(' ', 1)[0]
    if DBSession.query(Asset).filter(Asset.md5==md5).first():
        print 'not importing %s, file already imported with md5 %s' % (original_abspath, md5)
        return None

    # copy the asset from it's original location into the asset store directory
    import_dir = os.path.join(md5[0:2], md5[2:4])
    import_absdir = os.path.join(ASSET_ROOT, import_dir)
    if not os.path.isdir(import_absdir):
        os.makedirs(import_absdir)
    original_basename = os.path.basename(original_abspath)
    import_path = os.path.join(import_dir, original_basename)
    import_abspath = os.path.join(import_absdir, original_basename)
    subprocess.check_call(['cp', original_abspath, import_abspath])

    # persist asset metadata to the db
    size = os.path.getsize(import_abspath)
    asset = Asset(import_path, md5, size, original_basename, original_abspath)
    print 'imported %s to %s size=%d md5=%s' % (original_abspath, import_abspath, size, md5)
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

def queue_transcoding(assets):
    for asset in assets:
        inpath = asset.path
        infile = os.path.join(ASSET_ROOT, inpath)
        rand4 = ''.join(random.choice(string.lowercase + string.digits) for i in xrange(4))
        outpath = '%s.%s.t360.flv' % (inpath, rand4)
        outfile = os.path.join(ASSET_ROOT, outpath)
        REDIS.rpush('resque:queue:transcode360',
                    json.dumps({'class': 'Transcode360', 'args': [asset.id, infile, outfile, outpath]}))

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
        queue_transcoding(new_assets)
    print 'done!'
