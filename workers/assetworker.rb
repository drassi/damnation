require 'rubygems'
require 'json'
require 'pg'

class DerivativeAsset

  def self.run_cmd(cmd, logfile)
    cmd += ' >> %s 2>&1' % logfile
    system cmd
    if $? != 0:
      logtail = IO.popen("tail -10 %s" % logfile).read.strip.split('\n')
      raise "Process returned %d, full log at %s, tail is %s" % [$?.to_i, logfile, JSON.dump(logtail)]
    end
  end

  def self.perform(asset_id, derivative_type, cmds, result_path, part)
    logfile = '/tmp/%s.log' % (0...8).map{65.+(rand(25)).chr}.join
    for cmd in cmds do
      self.run_cmd cmd, logfile
    end
    db = PG.connect(:dbname => 'damnation', :user => 'damnation')
    db.exec 'insert into derivative_assets ("asset_id", "derivative_type", "path", "cmd", "output", "part", "created") values ($1, $2, $3, $4, $5, $6, now())',
             [asset_id, derivative_type, result_path, JSON.dump(cmds), logfile, part]
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
