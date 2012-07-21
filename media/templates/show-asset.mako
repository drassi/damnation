<%inherit file='base.mako'/>

<%block name='header'>
    <script src="/static/flowplayer/flowplayer-3.2.10.min.js"></script>
    <script src="/static/flowplayer/flowplayer.playlist-3.2.9.min.js"></script>
    <link rel="stylesheet" type="text/css" href="/static/css/asset.css"></link>
    <link rel="stylesheet" type="text/css" href="/static/bootstrap-wysihtml5-0.0.2/bootstrap-wysihtml5-0.0.2.css"></link>
    <script src="/static/bootstrap-wysihtml5-0.0.2/libs/js/wysihtml5-0.3.0_rc2.min.js"></script>
    <script src="/static/bootstrap-wysihtml5-0.0.2/bootstrap-wysihtml5-0.0.2.min.js"></script>
    <script src="/static/jquery/jquery.scrollTo.js"></script>
    <script src="/static/jquery/jquery-ui.min.js"></script>
</%block>

    <div style="width: 960px;margin-left:auto;margin-right:auto;position:relative;">

      <div class="asset-header">
        <span class="asset-title">${asset.title}</span>
        <span class="asset-added">Added ${asset.imported.strftime('%B %d, %Y').replace(' 0', ' ')}</span>
      </div>

      <a style="display:block;width:720px;height:480px;margin-bottom:6px;" id="player_${asset.id}"></a>
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

        var username = '${user.username}';
        var saveAnnotationURL = "${request.route_path('save-annotation', asset_id=asset.id)}";
        var deleteAnnotationURL = "${request.route_path('delete-annotation', annotation_id='ANNOTATION_ID')}";
        var assetId = "${asset.id}";

        var cuePoints = {
        % for annotation in annotations:
          '${annotation.id}' : {'time' : ${annotation.time},
                                'text' : '${annotation.text}',
                                'author' : '${annotation.user.username}',
                                'created' : '${annotation.created_str()}',
                                'deletable' : ${'true' if annotation.deletable else 'false'}}
          % if not loop.last:
          ,
          % endif
        % endfor
        };

        var cuePointIdList = [
        % for annotation in annotations:
          {'time' : ${annotation.time}, 'id' : '${annotation.id}'}
          % if not loop.last:
          ,
          % endif
        % endfor
        ];

        $(function() {

          $.each(cuePointIdList, function(i, cuepoint) {
            $('div#annotations').append(createAnnotation(cuepoint.id, cuePoints[cuepoint.id]));
          })
          if (cuePointIdList.length) {
            video.onCuepoint(cuePointIdList, cueAnnotation);
          }

          $('form#add-annotation').submit(function () {
            var text = $.trim($(this).find('input.add-annotation').val());
            var time = Number(video.getTime()) * 1000 + 100;
            if (text && !isNaN(time)) {
              $(this).find('input.add-annotation').val('');
              $.post(saveAnnotationURL, {'asset' : assetId, 'time' : time, 'text' : text}, saveAnnotationCallback, 'json');
            }
            return false;
          });

          $('div#annotations').on('click', 'button.annotation-delete', function() {
            if (confirm('Are you sure you want to delete this annotation?')) {
              var annotationId = $(this).parents('div.annotation').data('id');
              var deleteURL = deleteAnnotationURL.replace('ANNOTATION_ID', annotationId);
              $.post(deleteURL, deleteAnnotationCallback, 'json');
            }
          });

          $('div#annotations').on('click', 'div.annotation', function(e) {
            if (!$(e.target).is('button.annotation-delete')) {
              var annotation = $(this);
              var time = annotation.data('time');
              video.seek(time / 1000);
            }
          });

        });

        function saveAnnotationCallback(cuepoint) {
          var cuepointId = cuepoint.id;
          var time = cuepoint.time;
          cuePoints[cuepointId] = cuepoint;
          video.onCuepoint([{'time' : time, 'id' : cuepointId}], cueAnnotation);
          var annotation = createAnnotation(cuepointId, cuepoint);
          var annotations = $('div#annotations').children('div.annotation');
          var placed = false;
          for (var i=0; i<annotations.length; i++) {
            var a = $(annotations[i]);
            if (a.data('time') > time) {
              a.before(annotation);
              placed = true;
              break;
            }
          }
          if (!placed) {
            $('div#annotations').append(annotation);
          }
          $('div#annotations').scrollTo(annotation, 600);
        }

        function deleteAnnotationCallback(data) {
          var annotationId = data.id;
          $('div#annotation-' + annotationId).remove();
          delete cuePoints[annotationId];
        }

        function createAnnotation(key, value) {
          var secs = Math.floor(value.time / 1000);
          var mins = Math.floor(secs / 60);
          secs = ("0" + (secs % 60)).slice(-2);
          var delbutton;
          if (value.deletable) {
            delbutton = $('<button>').addClass('close').addClass('annotation-delete').html('&times;');
          } else {
            delbutton = $('<span>').html('&nbsp');
          }
          var annotation = $('<div>').attr('id', 'annotation-' + key)
                                     .addClass('annotation')
                                     .append($('<span>').addClass('annotation-time').text(mins + ':' + secs))
                                     .append($('<span>').addClass('annotation-spacer').html('&nbsp;'))
                                     .append($('<span>').addClass('annotation-text').text(value.text))
                                     .append($('<span>').addClass('annotation-spacer').html('&nbsp;'))
                                     .append($('<span>').addClass('annotation-author').text(value.author).attr('title', value.author))
                                     .append($('<span>').addClass('annotation-spacer').html('&nbsp;'))
                                     .append($('<span>').addClass('annotation-created').text(value.created))
                                     .append($('<span>').addClass('annotation-delete').append(delbutton));
          annotation.data('time', value.time);
          annotation.data('id', key);
          return annotation;
        }

        function cueAnnotation(clip, cuepointId) {
          var time = cuepointId.time;
          var id = cuepointId.id;
          var annotation = $('div#annotation-' + id);
          if (annotation.length) {
            if (!$('div#annotations').is(':hover')) {
              $('div#annotations').scrollTo(annotation, 600);
            }
            annotation.animate({
              'backgroundColor': '#DDD'
            }, 600);
            setTimeout(clearHighlight, 2000, annotation);
          }
        }

        function clearHighlight(e) {
          e.animate({
            'backgroundColor': 'white'
          }, 600);
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
            <input class="add-annotation" type="text" name="text" value="" maxlength="240" placeholder="Add a timed annotation here... (240-character limit)"></input><button type="submit" class="btn">Add</button>
          </div>
        </form>
        <div id="annotations"></div>
      </div>
    </div>
