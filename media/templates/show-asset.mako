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

        var username = 'username';

        var cuePoints = {
            'ni6td4' : {'time' : 3000, 'text' : 'Call me Ishmael. Some years ago- never mind how long precisely- having little or no money in my purse, and nothing particular to interest me on shore, I thought I would sail about a little and see the watery part of the world.', 'author' : 'dan', 'created' : '1 day'},
            'nogm6o' : {'time' : 8000, 'text' : 'It is a way I have of driving off the spleen and regulating the circulation. Whenever I find myself growing grim about the mouth;', 'author' : 'tom', 'created' : '7 days'},
            'tqn2jl' : {'time' : 12000, 'text' : 'whenever it is a damp, drizzly November in my soul; whenever I find myself involuntarily pausing before coffin warehouses, and bringing up the rear of every funeral I meet;', 'author' : 'sam', 'created' : '1 hour'},
            'asdf12' : {'time' : 13000, 'text' : 'and especially whenever my hypos get such an upper hand of me, that it requires a strong moral principle to prevent me from deliberately stepping into the street, and methodically knocking peoples hats off', 'author' : 'bob', 'created' : '2 years'},
            'nis6td4' : {'time' : 15000, 'text' : 'This is my substitute for pistol and ball. With a philosophical flourish Cato throws himself upon his sword; I quietly take to the ship. There is nothing surprising in this.', 'author' : 'john', 'created' : '1 day'},
            'nogasdfm6o' : {'time' : 20000, 'text' : 'There now is your insular city of the Manhattoes, belted round by wharves as Indian isles by coral reefs- commerce surrounds it with her surf.', 'author' : 'ted', 'created' : '7 days'},
            'tqn2fdjl' : {'time' : 28000, 'text' : 'Right and left, the streets take you waterward. Its extreme downtown is the battery, where that noble mole is washed by waves, and cooled by breezes, which a few hours previous were out of sight of land. Look at the crowds of water-gazers there.', 'author' : 'mike', 'created' : '1 hour'},
            'asdffdf12' : {'time' : 30000, 'text' : 'Circumambulate the city of a dreamy Sabbath afternoon. Go from Corlears Hook to Coenties Slip, and from thence, by Whitehall, northward. What do you see?', 'author' : 'lisa', 'created' : '2 years'}
        };

        $(function() {

          var cuePointIdList = [];
          $.each(cuePoints, function (key, value) {
            var annotation = createAnnotation(key, value);
            $('div#annotations').append(annotation);
            cuePointIdList.push({'time' : value.time, 'id' : key});
          })
          video.onCuepoint(cuePointIdList, cueAnnotation);

          $('form#add-annotation').submit(function () {
            var text = $.trim($(this).find('input.add-annotation').val());
            var time = Number(video.getTime()) * 1000 + 100;
            if (text && !isNaN(time)) {
              $(this).find('input.add-annotation').val('');
              var cuepointId = Math.random().toString(36).substring(2,8);
              var cuepoint = {'time' : time, 'text' : text, 'author' : username, 'created' : 'just now'};
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
            return false;
          });

          $('div#annotations').on('click', 'div.annotation', function() {
            var annotation = $(this);
            var time = annotation.data('time');
            video.seek(time / 1000);
          });

        });

        function createAnnotation(key, value) {
          var secs = Math.floor(value.time / 1000);
            var mins = Math.floor(secs / 60);
            secs = ("0" + (secs % 60)).slice(-2);
            var annotation = $('<div>').attr('id', 'annotation-' + key)
                                       .addClass('annotation')
                                       .append($('<span>').addClass('annotation-time').text(mins + ':' + secs))
                                       .append($('<span>').addClass('annotation-text').text(value.text))
                                       .append($('<span>').addClass('annotation-author').text(value.author))
                                       .append($('<span>').addClass('annotation-created').text(value.created))
                                       .append($('<span>').addClass('annotation-delete').append($('<button>').addClass('close').html('&times;')));
            annotation.data('time', value.time);
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
