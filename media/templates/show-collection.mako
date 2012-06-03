<%inherit file='base.mako'/>

<%block name='header'>
    <link rel="stylesheet" type="text/css" href="/static/css/list.css"></link>
    <script language="javascript">
      $(function() {
        $('img.screenshot').hover(hoverOnScreenshot, hoverOffScreenshot);
        $('img.screenshot').click(clickAsset);
        $('input.asset-checkbox').change(selectCheckbox);
        $('form#moveAssets').submit(submitMoveForm);
      });

      function hoverOnScreenshot(e) {
        var self = $(this);
        self.attr('src', self.data('moving-src'));
      }

      function hoverOffScreenshot(e) {
        var self = $(this);
        self.attr('src', self.data('still-src'));
      }

      function clickAsset(e) {
        window.location.href = $(this).parents('div.asset-container').data('asset-url');
      }

      function selectCheckbox(e) {
        var numSelected = $('input.asset-checkbox:checked').length;
        if (numSelected) {
          $('span#numAssetsSelected').text(numSelected);
          $('div#actionContainer').show();
        } else {
          $('div#actionContainer').hide();
        }
      }

      function submitMoveForm(e) {
        var asset_ids = [];
        $('input.asset-checkbox:checked').each(function() {
          var asset_id = $(this).data('asset-id');
          asset_ids.push(asset_id);
        });
        var targetCollectionId = $('option.targetCollection:selected').val();
        $.ajax({
          type: 'POST',
          url: $('form#moveAssets').attr('action'),
          dataType: 'json',
          data: {'asset_id' : asset_ids, 'collection_id' : targetCollectionId},
          success: moveSuccess
        });
        return false;
      }

      function moveSuccess(e) {
        window.location = window.location;
      }
    </script>
</%block>

    <div>Collection <b>${collection.name}</b></div>
    <div>Description: ${collection.description}</div>
    % if show_admin_link:
    <div><a href="${request.route_path('admin-collection', collection_id=collection.id)}">Admin collection</a></div>
    % endif
    <div><a href="${request.route_path('list-collections')}">Back to all collections</a></div>
    <div id="actionContainer" style="display: none;">
      Move
      <span id="numAssetsSelected"></span>
      selected assets to
      <form id="moveAssets" action="${request.route_path('move-assets')}" method="post">
        <select name="targetCollection">
          % for c in admin_collections:
            <option class="targetCollection" value="${c.id}">${c.name}</option>
          % endfor
        </select>
        <input type="submit" name="submit" value="Move" />
      </form>
    </div>
    % for asset in page_assets:
      <div class="asset-container" data-asset-id="{asset.id}" data-asset-url="${request.route_path('show-asset', asset_id=asset.id)}">
        <div>
          <div><img class="screenshot" src="${base_media_url}/${asset.thumbnail}" data-still-src="${base_media_url}/${asset.thumbnail}" data-moving-src="${base_media_url}/${asset.screenshot}"></img></div>
          <div>
              % if show_asset_checkboxes:
                <input type="checkbox" class="asset-checkbox" data-asset-id="${asset.id}" />
              % endif
              ${asset.title}
          </div>
          <div>${asset.duration}sec ${asset.width}x${asset.height} ${asset.size_mb_str()}MB</div>
          <div>Added ${asset.imported}</div>
        </div>
      </div>
    % endfor
