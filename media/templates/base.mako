<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" xmlns:tal="http://xml.zope.org/namespaces/tal">
  <head>
    <meta http-equiv="Content-Type" content="text/html;charset=UTF-8"/>
    <title>collections</title>
    <script src="/static/jquery/jquery-1.7.2.min.js"></script>
    <script src="/static/bootstrap/js/bootstrap.min.js"></script>
    <link rel="stylesheet" type="text/css" href="/static/css/base.css"></link>
    <link rel="stylesheet" type="text/css" href="/static/bootstrap/css/bootstrap.min.css"></link>
    <%block name='header'/>
  </head>
  <body>
    <div id="header">
      <span><a href="${request.route_path('list-collections')}">Home</a></span>
     % if is_user_admin:
      <span><a href="${request.route_path('admin-users')}">Admin users</a></span>
     % endif
      <span id="welcome">
        Welcome, ${user.username}!
        (<a href="${request.route_path('logout')}">logout</a>)
      </span>
    </div>
    <hr />
    <div id="page">
      ${self.body()}
    </div>
  </body>
</html>
