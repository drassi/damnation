<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" xmlns:tal="http://xml.zope.org/namespaces/tal">
  <head>
    <meta http-equiv="Content-Type" content="text/html;charset=UTF-8"/>
    <title>assets</title>
    <script src="/static/flowplayer/flowplayer-3.2.9.min.js"></script>
    <script src="/static/jquery/jquery-1.7.2.min.js"></script>
    <script language="javascript">
      $(function() {
        $('img.screenshot').hover(hoverOnScreenshot, hoverOffScreenshot);
      });

      function hoverOnScreenshot(e) {
        var self = $(this);
        self.attr('src', self.data('moving-src'));
      }

      function hoverOffScreenshot(e) {
        var self = $(this);
        self.attr('src', self.data('still-src'));
      }
    </script>
  </head>
  <body>
    % for asset in page_assets:
      <div class="asset-container" data-asset-id="{asset.id}" style="float: left;">
        <div>
          <div><img class="screenshot" src="${base_media_url}/${asset.thumbnail}" data-still-src="${base_media_url}/${asset.thumbnail}" data-moving-src="${base_media_url}/${asset.screenshot}"></img></div>
          <div>${asset.title}</div>
          <div>${asset.duration}sec ${asset.width}x${asset.height} ${asset.size_mb_str()}MB</div>
          <div>Added ${asset.created}</div>
          <div><a href="/static/assets/${asset.path}" target="_blank">Download original</a></div>
        </div>
      </div>
    % endfor
  </body>
</html>
