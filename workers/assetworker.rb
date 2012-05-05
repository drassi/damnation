require 'rubygems'
require 'json'
require 'open4'
require 'sqlite3'

SQLITE_DB = '/home/dan/dam/damnation/media.db'

class DerivativeAsset

  def self.run_cmd(cmd)
    pid, stdin, stdout, stderr = Open4.popen4 cmd
    ignored, status = Process::waitpid2 pid
    ret = status.to_i
    output = {'stdout' => stdout.read.split(/\n+/), 'stderr' => stderr.read.split(/\n+/)}
    if ret != 0:
      raise JSON.dump output
    end
    return output
  end

  def self.perform(asset_id, derivative_type, cmds, result_path)
    output = []
    for cmd in cmds do
      output.push self.run_cmd cmd
    end
    committed = false
    while !committed:
        begin
            db = SQLite3::Database.new SQLITE_DB
            db.execute 'insert into derivative_assets ("asset_id", "derivative_type", "path", "cmd", "output", "created") values (?, ?, ?, ?, ?, date("now"))',
                        asset_id, derivative_type, result_path, JSON.dump(cmds), JSON.dump(output)
            committed = true
        rescue
            sleep(rand(50) * 1.0 / 10)
        end
    end
  end
end

class TranscodeAsset < DerivativeAsset
  @queue = :transcode
end

class ScreenshotAsset < DerivativeAsset
  @queue = :screenshot
end

class ThumbnailAsset < DerivativeAsset
  @queue = :thumbnail
end
