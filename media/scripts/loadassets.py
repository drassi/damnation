import os
import sys
import transaction

from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from ..models import (
    DBSession,
    Asset,
    Base,
    )

def load_assets(asset_root):
    for dirpath, dirnames, filenames in os.walk(asset_root):
        for filename in filenames:
            path = os.path.abspath(os.path.join(dirpath, filename))
            if DBSession.query(Asset).filter(Asset.path==path).first():
                continue
            size = os.path.getsize(path)
            asset = Asset(path, size, filename)
            DBSession.add(asset)

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
    with transaction.manager:
        load_assets(asset_path)
