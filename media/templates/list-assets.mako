<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" xmlns:tal="http://xml.zope.org/namespaces/tal">
  <head>
    <meta http-equiv="Content-Type" content="text/html;charset=UTF-8"/>
    <title>assets</title>
    <script src="/static/flowplayer/flowplayer-3.2.9.min.js"></script>
  </head>
  <body>
    % for asset in assets:
      ${asset.id} ${asset.path} ${asset.size} ${asset.title} ${asset.created}<br />
      % for derivative in asset.derivatives:
        <a href="/static/assets/${derivative.path}" style="display:block;width:640px;height:360px;" id="player_${derivative.id}"></a>
        <script language="JavaScript">flowplayer("player_${derivative.id}", "/static/flowplayer/flowplayer-3.2.10.swf");</script>
      % endfor
      <a href="/static/assets/${asset.path}" target="_blank">Download original</a>
    % endfor
  </body>
</html>
