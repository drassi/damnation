<%inherit file='base.mako'/>

<%block name='header'>
    <link rel="stylesheet" type="text/css" href="/static/css/list.css"></link>
</%block>

Your collections:
% for collection, count, is_admin in collections:
  <div>
    <a href="${request.route_path('show-collection', collection_id=collection.id)}">${collection.name}</a> (${count} items)
      % if is_admin and count == 0:
        <form style="display: inline;" action="${request.route_path('delete-collection', collection_id=collection.id)}" method="post">
          <input type="submit" name="submit" value="Delete" />
        </form>
      % endif
  </div>
% endfor
% if show_add_collection_link:
  <form action="${request.route_path('add-collection')}" method="post">
    New collection:
    <input type="text" name="new_collection_name" value="" />
    <input type="submit" name="submit" value="Create new collection" />
  </form>
% endif
