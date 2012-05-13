<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" xmlns:tal="http://xml.zope.org/namespaces/tal">
  <head>
    <meta http-equiv="Content-Type" content="text/html;charset=UTF-8"/>
    <title>collections</title>
    <script src="/static/jquery/jquery-1.7.2.min.js"></script>
    <link rel="stylesheet" type="text/css" href="/static/css/list.css"></link>
  </head>
  <body>
    % for collection in collections:
      <div>
        <a href="${request.route_path('show-collection', id=collection.id)}">${collection.name}</a>
      </div>
    % endfor
  </body>
</html>
