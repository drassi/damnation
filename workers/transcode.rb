require 'rubygems'
require 'json'
require 'open4'
require 'sqlite3'

# save row in derivative_assets with:
#  * infile id
#  * outfile path
#  * cmd
#  * output
# todo
#  * insert via sqlite
#  * generate random outfile name
#  * delete outfile on failure

SQLITE_DB = '/home/dan/dam/damnation/media.db'

class Transcode360
  @queue = :transcode360

  def self.perform(asset_id, infile, outfile, outpath)
    type = "transcode"
    format = "flv"
    cmd = "ffmpeg -i %s -f flv -vf 'scale=-1:360' -r 15 -b 700 -g 10 -acodec libmp3lame -ar 22050 -ab 48000 -ac 1 -y %s" % [infile, outfile]
    pid, stdin, stdout, stderr = Open4.popen4 cmd
    ignored, status = Process::waitpid2 pid
    ret = status.to_i
    output = JSON.dump({'stdout' => stdout.read.split(/\n+/), 'stderr' => stderr.read.split(/\n+/)})
    if ret != 0:
      raise output
    end
    db = SQLite3::Database.new SQLITE_DB
    db.execute 'insert into derivative_assets ("asset_id", "path", "cmd", "output", "created") values (?, ?, ?, ?, date("now"))', asset_id, outpath, cmd, output
  end
end
