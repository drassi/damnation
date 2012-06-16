<%inherit file='base.mako'/>

<%block name='header'>
    <script src="/static/flowplayer/flowplayer-3.2.10.min.js"></script>
    <script src="/static/flowplayer/flowplayer.playlist-3.2.9.min.js"></script>
    <link rel="stylesheet" type="text/css" href="/static/css/asset.css"></link>
    <link rel="stylesheet" type="text/css" href="/static/bootstrap-wysihtml5-0.0.2/bootstrap-wysihtml5-0.0.2.css"></link>
    <script src="/static/bootstrap-wysihtml5-0.0.2/libs/js/wysihtml5-0.3.0_rc2.min.js"></script>
    <script src="/static/bootstrap-wysihtml5-0.0.2/bootstrap-wysihtml5-0.0.2.min.js"></script>
</%block>

    <div style="width: 778px;margin-left:auto;margin-right:auto;position:relative;">
      <a style="display:block;width:778px;height:480px;" id="player_${asset.id}"></a>
       % if asset.playlist:
        <div id="playlist" style="position:absolute; right:-70px; top:0px;">
         % for transcode in asset.transcodes:
          <a class="playlist-item" href="${base_media_url}/${transcode}">
            Part ${loop.index + 1}
          </a>
         % endfor
        </div>
        <script type="text/javascript">
          $(function() {
            flowplayer(
              "player_${asset.id}",
              "/static/flowplayer/flowplayer-3.2.11.swf",
              {
                clip : {
                  provider : 'provider'
                },
                plugins : {
                  provider : {
                    url : '/static/flowplayer/flowplayer.pseudostreaming-3.2.9.swf'
                  },
                  controls : {
                    playlist : true
                  }
                }
              }
            ).playlist('div#playlist', { continuousPlay : true, progressClass: 'loading' });
            $('textarea#description').wysihtml5();
          });
        </script>
       % else:
        <script type="text/javascript">
          $(function() {
            flowplayer(
              "player_${asset.id}",
	      "/static/flowplayer/flowplayer-3.2.11.swf",
              {
                clip : {
                  url : '${base_media_url}/${asset.transcode}',
                  provider : 'provider'
                },
                plugins : {
                  provider : {
                    url : '/static/flowplayer/flowplayer.pseudostreaming-3.2.9.swf'
                  }
                }
              }
            );
            $('textarea#description').wysihtml5();
          });
        </script>
       % endif
      <div class="asset-container" data-asset-id="{asset.id}" style="float: left;">
        <div>
          <h4>
            <span>${asset.title}</span>
            <span style="float: right;">Added ${asset.imported}</span>
          </h4>
          <div>${asset.original_abspath}</div>
          <div>${asset.duration}sec ${asset.width}x${asset.height} ${asset.size_mb_str()}MB</div>
          <div>${asset.description}</div>
          <div>From collection <a href=${request.route_path('show-collection', collection_id=asset.collection.id)}>${asset.collection.name}</a></div>
          % if asset.youtube:
            % for video_id in asset.youtube:
              <div><a href="http://www.youtube.com/watch?v=${video_id}">Watch on the Youtube</a></div>
            % endfor
          % endif
          % if show_modify_asset:
            <div>
              Modify asset:
              <form action="${request.route_path('modify-asset', asset_id=asset.id)}" method="post">
                <div>
                  Asset title:
                  <input type="text" name="asset_title" value="${asset.title}" />
                </div>
                <div>
                  Asset description:
                  <textarea id="description" name="asset_description" style="width: 100%;">${asset.description}</textarea>
                </div>
                <input type="submit" name="submit" value="Save changes to asset" />
              </form>
            </div>
          % endif
        </div>
      </div>
    </div>
