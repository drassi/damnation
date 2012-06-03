<%inherit file='base.mako'/>

    <div><a href="${request.route_path('list-collections')}">Back to collections</a></div>
    <form action="${request.route_path('admin-users-save')}" method="post">
      <p>
        % for user in users:
          <div>
            ${user.username}
            <input type="radio" name="usertype_${user.id}" id="usertype_${user.id}_normal" value="normal" ${'checked ' if user.active and not user.superuser else ''}/>
            <label for="usertype_${user.id}_normal">Normal user</label>
            <input type="radio" name="usertype_${user.id}" id="usertype_${user.id}_superuser" value="superuser" ${'checked ' if user.active and user.superuser else ''}/>
            <label for="usertype_${user.id}_superuser">Super user</label>
            <input type="radio" name="usertype_${user.id}" id="usertype_${user.id}_inactive" value="inactive" ${'checked ' if not user.active else ''}/>
            <label for="usertype_${user.id}_inactive">Inactive user</label>
          </div>
        % endfor
      </p>
      <p>
        <div>
          New user name:
          <input type="text" name="new_username" value="" />
        </div>
        <div>
          Password:
          <input type="password" name="new_password" value="" />
        </div>
      </p>
      <p>
        <div>
          <input type="submit" name-"submit" value="Save user changes" />
        </div>
      </p>
    </form>
