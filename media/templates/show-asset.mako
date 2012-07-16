<%inherit file='base.mako'/>

<%block name='header'>
    <script src="/static/flowplayer/flowplayer-3.2.10.min.js"></script>
    <script src="/static/flowplayer/flowplayer.playlist-3.2.9.min.js"></script>
    <link rel="stylesheet" type="text/css" href="/static/css/asset.css"></link>
    <link rel="stylesheet" type="text/css" href="/static/bootstrap-wysihtml5-0.0.2/bootstrap-wysihtml5-0.0.2.css"></link>
    <script src="/static/bootstrap-wysihtml5-0.0.2/libs/js/wysihtml5-0.3.0_rc2.min.js"></script>
    <script src="/static/bootstrap-wysihtml5-0.0.2/bootstrap-wysihtml5-0.0.2.min.js"></script>
    <script src="/static/jquery/jquery.scrollTo.js"></script>
</%block>

    <div style="width: 778px;margin-left:auto;margin-right:auto;position:relative;">

      <div class="asset-header">
        <span class="asset-title">${asset.title}</span>
        <span class="asset-added">Added ${asset.imported.strftime('%B %d, %Y').replace(' 0', ' ')}</span>
      </div>

      <a style="display:block;width:778px;height:480px;margin-bottom:6px;" id="player_${asset.id}"></a>
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
            video = flowplayer(
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
            video = flowplayer(
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
      <script type="text/javascript">

        username = 'username';

        cuePoints = {
            'ni6td4' : {'time' : 1230, 'text' : 'first annotation', 'author' : 'dan', 'created' : '1 day'},
            'nogm6o' : {'time' : 2340, 'text' : 'When a form is submitted through submit button click the form data is subsequently cleared or reset . But when we submit a form by AJAX then we have t', 'author' : 'tom', 'created' : '7 days'},
            'tqn2jl' : {'time' : 4200, 'text' : 'test kajskjdfklj kljasdifjaij4fha34h aiuhwf78a844h4g98 h3498gh 8ah3489g89 herfasdhfh a89wehf89a', 'author' : 'doogie', 'created' : '1 hour'},
            'asdf12' : {'time' : 10000, 'text' : 'this is a slightly longer annotation with no reasonabe explanation', 'author' : 'doogie', 'created' : '2 years'},
            'nis6td4' : {'time' : 12345, 'text' : 'first annotation', 'author' : 'dan', 'created' : '1 day'},
            'nogasdfm6o' : {'time' : 12346, 'text' : 'When a form is submitted through submit button click the form data is subsequently cleared or reset . But when we submit a form by AJAX then we have to c', 'author' : 'tom', 'created' : '7 days'},
            'tqn2fdjl' : {'time' : 12347, 'text' : 'test kajskjdfklj kljasdifjaij4fha34h aiuhwf78a844h4g98 h3498gh 8ah3489g89 herfasdhfh a89wehf89a', 'author' : 'doogie', 'created' : '1 hour'},
            'asdffdf12' : {'time' : 12348, 'text' : 'this is a slightly longer annotation with no reasonabe explanation', 'author' : 'doogie', 'created' : '2 years'}
        };

        $(function() {

          var cuePointIdList = [];
          $.each(cuePoints, function(key, value) {
            var secs = Math.floor(value.time / 1000);
            var mins = Math.floor(secs / 60);
            secs = ("0" + (secs % 60)).slice(-2);
            var annotation = $('<div>').attr('id', 'annotation-' + key)
                                       .addClass('annotation')
                                       .append($('<span>').addClass('annotation-time').text(mins + ':' + secs))
                                       .append($('<span>').addClass('annotation-text').text(value.text))
                                       .append($('<span>').addClass('annotation-author').text(value.author))
                                       .append($('<span>').addClass('annotation-created').text(value.created));
            $('div#annotations').append(annotation);
            cuePointIdList.push({'time' : value.time, 'id' : key});
          });

          video.onCuepoint(cuePointIdList, cueAnnotation);

          $('form#add-annotation').submit(function () {
            var text = $(this).find('input.add-annotation').val();
            var time = Number(video.getTime());
            if (!isNaN(time)) {
              $(this).find('input.add-annotation').val('');
              var cuepointId = Math.random().toString(36).substring(2,8);
              var cuepoint = {'time' : time * 1000, 'text' : text, 'author' : username};
              cuePoints[cuepointId] = cuepoint;
              video.onCuepoint([{'time' : time * 1000 + 100, 'id' : cuepointId}], cueAnnotation);
            }
            return false;
          });

        });

        function cueAnnotation(clip, cuepointId) {
          var time = cuepointId.time;
          var id = cuepointId.id;
          var annotation = $('div#annotation-' + id);
          if (annotation.length) {
            $('div#annotations').scrollTo(annotation, 600);
          }
        }

        function rm(e) {
          e.remove();
        }
      </script>
      <div class="asset-container" data-asset-id="{asset.id}">
        <div>
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
      <div class="annotation-container">
        <form id="add-annotation">
          <div class="input-append">
            <input class="add-annotation" type="text" name="text" value="" maxlength="160" placeholder="Add a timed annotation here... (160-character limit)"></input><button type="submit" class="btn">Add</button>
          </div>
        </form>
        <div id="annotations"></div>
      </div>
    </div>
