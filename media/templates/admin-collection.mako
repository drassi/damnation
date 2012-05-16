<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" xmlns:tal="http://xml.zope.org/namespaces/tal">
  <head>
    <meta http-equiv="Content-Type" content="text/html;charset=UTF-8"/>
    <title>admin collection</title>
    <script src="/static/jquery/jquery-1.7.2.min.js"></script>
    <link rel="stylesheet" type="text/css" href="/static/css/list.css"></link>
  </head>
  <body>
    <form action="${request.route_path('admin-collection-save', collection_id=collection.id)}" method="post">
      Administer collection <b>${collection.name}</b>, <a href="${request.route_path('show-collection', collection_id=collection.id)}">click here</a> to return to the collection without saving.
      <p>
        Rename collection:
        <input type="text" name="collection_name" value="${collection.name}" />
      </p>
      <p>
        Edit description:
        <textarea name="collection_description">${collection.description}</textarea>
      </p>
      <p>
        Change or revoke current permissions:<br />
        <small>(Read allows a user to view the collection, Write allows metadata modification of assets in the collection, Admin allows modification of collection assets, users and metadata)</small>
       % for user_id, user_name, grant_type in grants:
        <div>
          ${user_name}
          <input type="radio" name="grant_${user_id}" id="grant_${user_id}_read" value="read" ${'checked ' if grant_type=='read' else ''}/>
          <label for="grant_${user_id}_read">Read</label>
          <input type="radio" name="grant_${user_id}" id="grant_${user_id}_write" value="write" ${'checked ' if grant_type=='write' else ''}/>
          <label for="grant_${user_id}_write">Write</label>
          <input type="radio" name="grant_${user_id}" id="grant_${user_id}_admin" value="admin" ${'checked ' if grant_type=='admin' else ''}/>
          <label for="grant_${user_id}_admin">Admin</label>
          <input type="radio" name="grant_${user_id}" id="revoke_${user_id}" value="revoke" />
          <label for="revoke_${user_id}">Revoke all permission</label>
        </div>
       % endfor
      </p>
      <p>
        Grant new permissions for an existing user:<br />
        <small>(Enter the user's exact username)</small>
        <div>
          <input type="text" name="new_username" value="" />
          <input type="radio" name="new_grant" id="new_grant_read" value="read" checked />
          <label for="new_grant_read">Read</label>
          <input type="radio" name="new_grant" id="new_grant_write" value="write" />
          <label for="new_grant_write">Write</label>
          <input type="radio" name="new_grant" id="new_grant_admin" value="admin" />
          <label for="new_grant_admin">Admin</label>
        </div>
      </p>
      <p>
        <input type="submit" name="submit" value="Save all changes to collection" />
      </p>
    </form>
  </body>
</html>
