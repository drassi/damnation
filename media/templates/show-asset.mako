<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" xmlns:tal="http://xml.zope.org/namespaces/tal">
  <head>
    <meta http-equiv="Content-Type" content="text/html;charset=UTF-8"/>
    <title>assets</title>
    <script src="/static/flowplayer/flowplayer-3.2.9.min.js"></script>
    <script src="/static/jquery/jquery-1.7.2.min.js"></script>
  </head>
  <body>
    <div style="width: 640px;margin-left:auto;margin-right:auto;">
      <a style="display:block;width:640px;height:360px;" id="player_${asset.id}"></a>
        <script language="JavaScript">
          flowplayer(
            "player_${asset.id}",
            "/static/flowplayer/flowplayer-3.2.10.swf",
            {
              clip : {
                url : '${base_media_url}/${asset.transcode}',
                provider : 'provider'
              },
              plugins : {
                provider : {
                  url : '/static/flowplayer/flowplayer.pseudostreaming-3.2.9.swf'
                }
              }
            }
          );
        </script>
      <div class="asset-container" data-asset-id="{asset.id}" style="float: left;">
        <div>
          <div>${asset.title}</div>
          <div>${asset.duration}sec ${asset.width}x${asset.height} ${asset.size_mb_str()}MB</div>
          <div>Added ${asset.created}</div>
          <div><a href="/static/assets/${asset.path}" target="_blank">Download original</a></div>
          % if asset.youtube:
            % for video_id in asset.youtube:
              <div><a href="http://www.youtube.com/watch?v=${video_id}">Watch on the Youtube</a></div>
            % endfor
          % endif
        </div>
      </div>
    </div>
  </body>
</html>
