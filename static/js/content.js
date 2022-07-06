/**
 * 
 * @authors Your Name (you@example.org)
 * @date    2021-07-11 09:07:34
 * @version $Id$
 */

function provideTags(tags,e,url,type,albumName){
	if (!document.getElementById('tc')){
		$('body').append('<div id="tc"></div>');
		$('#tc').css('position','fixed');
		$('#tc').css('display','flex');
		$('#tc').css('flex-direction','row');
		$('#tc').css('flex-wrap','wrap ');
		$('#tc').css('overflow-y','scroll');
		$('#tc').css('margin-left','300px');
		$('#tc').css('margin-right','300px');
		$('#tc').css('background-color','rgb(109, 106, 99, 0.5)');
		$('#tc').css('top','20%');
		$('#tc').css('left','220px;');
		for (var i=0;i<tags.length;i++){
			$('#tc').append('<div class="tags">'+tags[i]+'</div>');
		}
		if (type == 'move'){
			$(".tags").bind("click",function(event){updateTags(e,url,event);$('#tc').remove();});
		}else{
			if(type == 'ADD'){
                    $(".tags").bind("click",function(event){operatealbum(e,url,'add',event);$('#tc').remove();});
			}else{
                if(type == 'move_'){
                    $(".tags").bind("click",function(event){operatealbum(e,url,'move',event,albumName);$('#tc').remove();});
                }
			}

		}
		
	}else{
		$('#tc').remove();
	}

}

function setMesbox(text,timing){
	var e = $(".mesbox")[0];
	e.innerHTML = "&nbsp"+text;
	if (timing != -1){
		setTimeout(function(){e.innerHTML = "~~~~~~~~";},timing*1000);
	}
}

function provideName(){
	$('#createAlbum').toggle();
}

function autoPlay(list,i){
	$('#vv').on('ended',function(){
		 i++;
	     if(i >= list.length){
	        i = 0;
	      }
	      var p = list[i];
	      this.src(p);
	      this.play();
    });
}

function showOrHide(event) {
    var t = event.target.parentNode.parentNode.nextElementSibling.style.display
    if(t=='none'){
        event.target.parentNode.parentNode.nextElementSibling.style.display='block'
    }else{
        event.target.parentNode.parentNode.nextElementSibling.style.display='none'
    }
}