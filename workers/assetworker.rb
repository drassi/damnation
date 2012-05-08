require 'rubygems'
require 'json'
require 'open4'
require 'pg'

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
    db = PG.connect(:dbname => 'damnation', :user => 'damnation')
    db.exec 'insert into derivative_assets ("asset_id", "derivative_type", "path", "cmd", "output", "created") values ($1, $2, $3, $4, $5, now()))',
             [asset_id, derivative_type, result_path, JSON.dump(cmds), JSON.dump(output)]
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
