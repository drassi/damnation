<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" xmlns:tal="http://xml.zope.org/namespaces/tal">
  <head>
    <meta http-equiv="Content-Type" content="text/html;charset=UTF-8"/>
    <title>assets</title>
  </head>
  <body>
    % for asset in assets:
      ${asset.id} ${asset.path} ${asset.size} ${asset.title} ${asset.created}<br />
    % endfor
  </body>
</html>
