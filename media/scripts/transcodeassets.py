import os
import sys
import time
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

def transcode_assets():
    while True:
        asset = DBSession.query(Asset).filter(Asset.transcoded360==0).first()
        if not asset:
            time.sleep(10)
            continue
        with transaction.manager:
            asset.transcoded360 = 1
            DBSession.flush()
        infile = asset.path
        outfile = asset.path + '.t360.flv'
        #os.system('ffmpeg -i %s -f flv -vf "scale=-1:360" -r 15 -b 700 -g 10 -acodec libmp3lame -ar 22050 -ab 48000 -ac 1 -y %s' % (infile, outfile))
        os.system('ffmpeg -i %s -f flv -s 480x360 -r 15 -b 700 -g 10 -acodec libmp3lame -ar 22050 -ab 48000 -ac 1 -y %s' % (infile, outfile))
        with transaction.manager:
            asset.transcoded360 = 2
            DBSession.flush()

def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd)) 
    sys.exit(1)

def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    transcode_assets()
