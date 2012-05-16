<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" xmlns:tal="http://xml.zope.org/namespaces/tal">
  <head>
    <meta http-equiv="Content-Type" content="text/html;charset=UTF-8"/>
    <title>admin collection</title>
    <script src="/static/jquery/jquery-1.7.2.min.js"></script>
    <link rel="stylesheet" type="text/css" href="/static/css/list.css"></link>
  </head>
  <body>
    <form action="${request.route_path('admin-collection-save', collection_id=collection_id)}" method="post">
      % for user_id, user_name, grant_type in grants:
        <div>
          ${user_name}
          <input type="radio" name="grant_${user_id}" id="grant_${user_id}_read" value="read" ${'checked ' if grant_type=='read' else ''}/>
          <label for="grant_${user_id}_read">Read</label>
          <input type="radio" name="grant_${user_id}" id="grant_${user_id}_write" value="write" ${'checked ' if grant_type=='write' else ''}/>
          <label for="grant_${user_id}_write">Write</label>
          <input type="radio" name="grant_${user_id}" id="grant_${user_id}_admin" value="admin" ${'checked ' if grant_type=='admin' else ''}/>
          <label for="grant_${user_id}_admin">Admin</label>
        </div>
      % endfor
      <input type="submit" name="submit" value="Save Permissions" />
    </form>
  </body>
</html>
