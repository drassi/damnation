require 'rubygems'
require 'json'
require 'open4'
require 'pg'
require 'tmpdir'
require 'shellwords'
require 'fileutils'

class YoutubeUpload

  @queue = :youtube

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

  def self.perform(asset_id, derivative_type, asset_abspath, split_cmd_path, upload_cmd_path, email, password, title, description, category)

    cmds = []
    output = []

    tmpdir = Dir.mktmpdir
    Dir.chdir tmpdir

    split_cmd = "%s %s" % [split_cmd_path, asset_abspath]
    split_output = self.run_cmd split_cmd
    cmds.push split_cmd
    output.push split_output

    upload_path_args = split_output['stdout'].join(' ')
    upload_cmd = "%s --email=%s --password=%s --title=%s --description=%s --category=%s %s" % [upload_cmd_path, Shellwords.escape(email), Shellwords.escape(password), Shellwords.escape(title), Shellwords.escape(description), Shellwords.escape(category), upload_path_args]
    upload_output = self.run_cmd upload_cmd
    cmds.push upload_cmd
    output.push upload_output

    result_video_urls = upload_output['stdout']
    video_ids = []
    for url in result_video_urls:
        url_match = url.match /^http:\/\/www\.youtube.com\/watch\?v=(.*)/
        if !url_match:
            raise url
        end
        video_ids << url_match[1]
    end
    if video_ids.length == 0:
        raise JSON.dump upload_output
    end
    db = PG.connect(:dbname => 'damnation', :user => 'damnation')
    db.execute 'insert into derivative_assets ("asset_id", "derivative_type", "path", "cmd", "output", "created") values ($1, $2, $3, $4, $5, now()))',
                [asset_id, derivative_type, JSON.dump(video_ids), JSON.dump(cmds), JSON.dump(output)]

    FileUtils.rm_rf tmpdir
  end
end
