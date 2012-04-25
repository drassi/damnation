<html>
  <head>
    <title>assets</title>
  </head>
  <body>
    % for asset in assets:
      ${asset.id} ${asset.path} ${asset.size} ${asset.name} ${asset.created}<br />
    % endfor
  </body>
</html>
