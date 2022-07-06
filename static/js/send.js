function send_mail(e,email,url,sendType){
    var data = JSON.stringify({
        'email': email,
        'sendType': sendType
    })
    $.ajax({
        url:url,
        type:"post",
        data:data,
        dataType: 'json',
        processData:false,
        contentType:'application/json',
        success:function(data){
        result = data['result']
            if(result=='success'){
                start_timer(e,60);
            }
        },
        error:function(e){
                alert("error"+e);
        }
    })
}
function start_timer(e,timing){
        e.attr("disabled",true);
        var index=timing;
        function timer(){
            index=index-1;
            if(index>0){
                var text = index+"秒后可重发";
                e.html(text);
                window.setTimeout(timer,1000);
            }else{
                e.attr("disabled",false);
                e.html("发送验证码");
            }
        }
        e.html("60秒后可重发");
        timer();
}
function edit_img(url,id,img,e,depth_e){
    var data = JSON.stringify({
        'id': id,
        'depth':depth_e.val()
    });
    $.ajax({
        url:url,
        type:"post",
        data:data,
        dataType: 'text',
        processData:false,
        contentType:'application/json',
        success:function(data){
            img.src=data;
            e.last=data;
        },
        error:function(e){
               alert("error"+e);
        }
    })
}
// 清空精彩一刻???
function clear_video(url){
    var data = JSON.stringify({
        'id': id,
        'depth':depth_e.val()
    });
    $.ajax({
        url:url,
        type:"post",
        data:data,
        dataType: 'text',
        processData:false,
        contentType:'application/json',
        success:function(data){
        },
        error:function(e){
               alert("error"+e);
        }
    })
}
// 自动检测
function detection(){
    $.ajax({
        url:'/classify',
        type:"post",
        dataType: 'json',
        processData:false,
        contentType:'application/json',
        success:function(data){
            name = data['threadName'];
            setMesbox("正在检测",-1);
            setTimeout(function(){judge(name);},5000);
        },
        error:function(e){
            alert("error"+e);
        }
    });
}
function judge(name,e){
    $.ajax({
        url:"/judgeclassify",
        type:"post",
        data:JSON.stringify({"threadName":name}),
        dataType: "json",
        processData:false,
        contentType:"application/json",
        success:function(data){
            isFinished = data["isFinished"];
            if(isFinished){
                setMesbox("检测完毕",7);
            }else{
                setTimeout(function(){judge(name,e);},5000);
            }
        },
        error:function(e){
               alert("error"+e);
        }
    });
}
// 移动
function updateTags(e,url,event){
    var a = new Array();
    e.each(function(){
        a.push(this.id);
    });
    data = JSON.stringify({'id_list':a,'new_tagName':event.target.innerText});
      $.ajax({
          type:'POST',
          url:url,
          processData:false,
          contentType:false,
          data:data,
          contentType:'application/json',
          success:function(data){
                alert('移动成功')
                window.location.href = data;
          }
      })
}
function faceTagRename(name1,name2,url){
    $.ajax({
          type:'POST',
          url:url,
          processData:false,
          contentType:false,
          data:JSON.stringify({'old_tagName':name1,'new_tagName':name2}),
          contentType:'application/json',
          success:function(data){
              alert(data);
              window.location.reload();
          }
      })
}
//图片重命名
function imageRename(id,name,url){
    $.ajax({
          type:'POST',
          url:url,
          processData:false,
          contentType:false,
          data:JSON.stringify({'id':id,'name':name}),
          contentType:'application/json',
          success:function(data){
              alert(data);
              window.location.reload();
          }
      })
}

function create_album(albumname,url){
    $.ajax({
        type:'POST',
        url:url,
        processData:false,
        contentType:false,
        data:JSON.stringify({'albumName':albumname}),
        contentType:'application/json',
        success:function(data){
            alert(data);
            window.location.reload();
        }
    })
}

function delete_album(albumname,url){
    $.ajax({
        type:'POST',
        url:url,
        processData:false,
        contentType:false,
        data:JSON.stringify({'albumName':albumname}),
        contentType:'application/json',
        success:function(data){
            alert(data);
            window.location.reload();
        }
    })
}

function operatealbum(e,url,t,event,albumName){
    var a = new Array();
    e.each(function(){
        a.push(this.id);
    });
    if(t == 'add'){
      $.ajax({
          type:'POST',
          url:url,
          processData:false,
          contentType:false,
          data:JSON.stringify({'id_list':a,'albumName':albumName?albumName:event.target.innerText}),
          contentType:'application/json',
          success:function(data){
              alert(data);
              window.location.reload();
          }
      })
  }else if(t == 'remove'){
      $.ajax({
          type:'POST',
          url:url,
          processData:false,
          contentType:false,
          data:JSON.stringify({'id_list':a,'albumName':albumName?albumName:event}),
          contentType:'application/json',
          success:function(data){
              alert(data);
              window.location.reload();
          }
      })
  }else if(t == 'move'){
        $.ajax({
          type:'POST',
          url:url,
          processData:false,
          contentType:false,
          data:JSON.stringify({'id_list':a,'albumName1':albumName,'albumName2':event.target.innerText}),
          contentType:'application/json',
          success:function(data){
              alert(data);
              window.location.reload();
          }
        })
  }
}
function albumRename(name1,name2,url){
    $.ajax({
          type:'POST',
          url:url,
          processData:false,
          contentType:false,
          data:JSON.stringify({'albumName1':name1,'albumName2':name2}),
          contentType:'application/json',
          success:function(data){
              alert(data);
              window.location.reload();
          }
      })
}
// 单张删除
function send_del(url,imgId){
  $.ajax({
      type:'POST',
      url:url,
      processData:false,
      contentType:false,
      data:JSON.stringify({'id':imgId}),
      contentType:'application/json',
      success:function(data){
          alert(data);
          window.close();
      }
  });
}
// 批量删除
function deleteImgs(e,url){
    var a = new Array();
    e.each(function(){
        a.push(this.id);
    });
      $.ajax({
          type:'POST',
          url:url,
          processData:false,
          contentType:false,
          data:JSON.stringify({'id':a}),
          contentType:'application/json',
          success:function(data){
              alert(data);
              window.location.reload();
          }
      })
}
// 批量下载
function downloadFiles(e){
    var a = new Array();
    var url=window.location.protocol+'//'+window.location.host+'/download/images';
    e.each(function(){
        a.push(this.id);
    });
    for (var i=0;i<a.length;i++){
        var aa = document.createElement('a');
        aa.download="test.png";
        aa.href = url+'/'+a[i];
        // aa.onclick = send_download(url+'/'+a[i]);
        $("body").append(aa);
        aa.click();
        $(aa).remove();
    }  
}
//批量上传
function uploadFiles(e){
    var a = new Array();
    e.each(function(){
        a.push(this.id);
    });
      $.ajax({
          type:'POST',
          url:url,
          processData:false,
          contentType:false,
          data:JSON.stringify({'id':a}),
          contentType:'application/json',
          success:function(data){
              alert(data);
              window.location.reload();
          }
      })
}
// 文件上传
function init(fileMd5,fileSuffix,$list,state,$btn,count,num,map,uploader){
    // 当有文件被添加进队列的时候
    uploader.on('fileQueued', function(file) {
        //保存文件扩展名
        fileSuffix=file.ext;
        fileName=file.source['name'];
        var fileSize=file.size;
        var fileSizeStr=WebUploader.Base.formatSize(fileSize);
        $list.append(
                '<tr id="' + file.id + '" class="item" flag=0>'+
                '<td class="index">' + num + '</td>'+
                '<td class="info">' + file.name + '</td>'+
                '<td class="size">' + fileSizeStr + '</td>'+
                '<td class="state">等待上传...</td>'+
                '<td class="operate"><button name="upload" class="btn btn-warning">开始</button><button name="delete" class="btn btn-error">删除</button></td></tr>');
        map.put(file.id+"",file);
        num++;
    });

    // 文件上传过程中创建进度条实时显示。
    uploader.on('uploadProgress', function(file, percentage) {
        $('#' + file.id).find('td.state').text(
                '上传中 ');
    });

    uploader.on('uploadSuccess', function(file) {
        $('#' + file.id).find('td.state').text('已上传');
        count++;
        var p = Math.ceil(count*100/num);
        $("#bar_p").html("<div style=\"background-color: orange;height:10px;width:"+p+"%;\"></div><span style=\"position: relative;top: -18px;\">"+p+"%</span>");
    });

    uploader.on('uploadError', function(file) {
        $('#' + file.id).find('td.state').text('上传出错');
    });

    uploader.on('uploadComplete', function(file) {
        uploader.removeFile(file);
    });


    uploader.on('all', function(type) {
        if (type === 'startUpload') {
            state = 'uploading';
        } else if (type === 'stopUpload') {
            state = 'paused';
        } else if (type === 'uploadFinished') {
            state = 'done';
        }

        if (state === 'uploading') {
            $btn.text('暂停上传');
        } else {
            $btn.text('开始上传');
        }
    });

    $btn.on('click', function(){
        if (state === 'uploading'){
            uploader.stop(true);
        } else {
            uploader.upload();
        }
    });
}

//回收站还原
function restoreImgs(e,url){
    var a = new Array();
    e.each(function(){
        a.push(this.id);
    });
      $.ajax({
          type:'POST',
          url:url,
          processData:false,
          contentType:false,
          data:JSON.stringify({'id':a}),
          contentType:'application/json',
          success:function(data){
              window.location.reload();
          }
      })
}
//清空回收站
function clearRecycle(url){
   $.ajax({
          type:'POST',
          url:url,
          processData:false,
          contentType:false,
          contentType:'application/json',
          success:function(data){
              window.location.reload();
          }
      })
}

//设置cookie
function setCookie(cname, cvalue, exdays) {
    var d = new Date();
    d.setTime(d.getTime() + (exdays*24*60*60*1000));
    var expires = "expires="+d.toUTCString();
    document.cookie = cname + "=" + cvalue + "; " + expires;
}
//获取cookie
function getCookie(cname) {
    var name = cname + "=";
    var ca = document.cookie.split(';');
    for(var i=0; i<ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1);
        if (c.indexOf(name) != -1) return c.substring(name.length, c.length);
    }
    return "";
}
//清除cookie  
function clearCookie(name) {  
    setCookie(name, "", -1);  
}

//显示弹窗
function openRegisterModal(t){
    var id = t + 'Modal';
    let e = $('#'+id);
    e.find('.registerBox').fadeIn('fast');
    e.find('.register-footer').fadeIn('fast');
    setTimeout(function(){
        e.modal('show');
        if(t=='set'){
            $.ajax({
              type:'POST',
              url:'/get/user',
              processData:false,
              success:function(data){
              console.log(data.avatar)
                  e.find('input[name=username]').val(data.user)
                  e.find('input[name=name]').val(data.name)
                  e.find('#facesetid').html(data.facesetid)
                  if(data.avatar){
                    $('#myAvatar').attr('src',data.avatar)
                    $('#nav-avatar').attr('src',data.avatar)
                  }
            }
      })
        }
    }, 230);

}

function loginAjax(){
    /*   Remove this comments when moving to server
    $.post( "/login", function( data ) {
            if(data == 1){
                window.location.replace("/home");
            } else {
                 shakeModal();
            }
        });
    */

/*   Simulate error message from the server   */
     shakeModal();
}

function shakeModal(){
    $('#loginModal .modal-dialog').addClass('shake');
             $('.error').addClass('alert alert-danger').html("Invalid email/password combination");
             $('input[type="password"]').val('');
             setTimeout( function(){
                $('#loginModal .modal-dialog').removeClass('shake');
    }, 1000 );
}

//检查弹窗
function check(e,t,url){
    e = $(e);
    var form = e.closest('form');
    if (t==1){
        var tt = '';
        var yx = '';
        form.children('input').each(function(i,x){
            x = $(x)
            if(x.attr('name')=='username' ){
                if($.trim(x.val())==''){
                    alert('邮箱不能为空');
                }else{
                    yx=x.val();
                }
            }
            if(x.attr('name')=='sendType' ){
                tt = parseInt(x.val())
            }
        });
        if(tt !== ''){
            send_mail(e,yx,url,tt);
        }
    }
    if(t==2){
        var isOK = true;
        var pwd = '';
         form.find('input').each(function(i,x){
            x = $(x)
            if(x.attr('name')=='username'){
                if($.trim(x.val())==''){
                    alert('邮箱不能为空！');
                    isOK = false;
                    return false;
                }
                var reg=new RegExp("^([\\.a-zA-Z0-9_-])+@([a-zA-Z0-9_-])+((\\.[a-zA-Z0-9_-]{2,3}){1,2})$");
                if(!reg.test(x.val())){
                    alert('请输入正确的邮箱！');
                    isOK = false;
                    return false;
                }
            }
            if(x.attr('name')=='name'){
                 if($.trim(x.val())==''){
                    alert('昵称不能为空！');
                    isOK = false;
                    return false;
                 }
                 if(!x.val().match(/([a-zA-Z0-9_]){2,15}$/)){
                    alert('昵称只能为英文或者数字或者下划线组成的2-15个字符！');
                    isOK = false;
                    return false;
                 }
            }
            if(x.attr('name')=='pwd'){
                 if($.trim(x.val())==''){
                    alert('密码不能为空！');
                    isOK = false;
                    return false;
                 }
                 pwd = x.val();
            }
            if(x.attr('name')=='password_confirmation'){
                 if($.trim(x.val())==''){
                    alert('新密码不能为空！');
                    isOK = false;
                    return false;
                 }
                 if(x.val() != pwd){
                    alert('密码与新密码不一致！');
                    isOK = false;
                    return false;
                 }
            }
            if(x.attr('name')=='code'){
                 if($.trim(x.val())==''){
                    alert('验证码不能为空！');
                    isOK = false;
                    return false;
                 }
            }
        });
        if(!isOK){
            return false;
        }
        var formData ;
        if(form.find("input[type='file']")){
            var f = form[0]
            formData = new FormData(f);
            console.log(formData.get("name"))
        }else{
            formData = form.serialize();
        }
        $.ajax({
			type: "post",
			url: url,
			data: formData,
			processData: false,
			contentType: false,
			dataType: "json", // 指定后台传过来的数据是json格式
			success: function(data){
                alert(data.mes);
                form.closest('.modal').modal('hide');
                if(url.includes('update')){
                    window.location.reload();
                }
			},
			error: function(err){
				alert("error");
			}
		})
        return false;
    }

}
//上传头像相关
function handleFiles(file) {
    file=file[0];
    var img = document.getElementById('myAvatar');
    var imageType = /^image\//;
    if ( !imageType.test(file.type) ) {
      return
    }
    img.classList.add("obj");
    img.file = file;
    var reader = new FileReader();
    reader.onload = (function(aImg) {
      return function(e) {
        aImg.src = e.target.result;
      };
    })(img);
    reader.readAsDataURL(file);
}


function getImageType(file){
    var types = {
        'PNG': '89 50',
        'JPG': 'ff d8',
        'ICO': '00 00 01 00 01 00 20 20',
        'GIF': '47 49 46',
        'BMP': '42 d4D',
        'TIFF': '4D 4D',
        'tiff': '49 49'
    }
    for (var x in types){
        var len = types[x].split(' ').length
        var ret  = this.blobToString(file.slice(0,len));
        if(ret == types[x]){
            return x;
        }
    }
    return false
}
function toBase64(file){
    var t = getImageType(file)
    if(t){
        return 'data:image/'+t+';base64,' + window.btoa(String.fromCharCode(...new Uint8Array(result)));
    }
    return t
}
//获得图片数据
async function getImages(files,userid) {
    console.log(new Date().getTime())
    let cool = document.getElementsByClassName('cool')[0]
    var index = 0
    for(var x in files){
        var div1 = document.createElement('div');
        var div2 = document.createElement('div');
        $(div1).append("<li class=\"date"+index+"\"><span onclick=\"showOrHide(event)\">"+x+"</span></li>");
        cool.appendChild(div1)
        div2.style.display = 'block';
        cool.appendChild(div2);
        for(var j=0;j<files[x].length;j++){
            y = files[x][j]
            var canvas = document.createElement('canvas');
            var need = document.createElement('div');
            var show_link = document.createElement('a');
            need.setAttribute("class", "need");
            canvas.setAttribute('id',y.id);
            canvas.setAttribute('class','show1');
            canvas.setAttribute('title',y.name);
            show_link.setAttribute('class','show_link');
            var ImageUrl = '/'+userid+'/Image/'+y.id;
            show_link.setAttribute('href',ImageUrl);
            show_link.setAttribute('target',"_blank");
            show_link.appendChild(canvas);
            need.appendChild(show_link);
            div2.appendChild(need);
            $(show_link).bind("click", function () {
                if($('.send').is(":hidden")){
                    $(this).click();
                    return false;
                }else{
                  $(this).children('.show1').toggleClass('selected');
                  counter();
                  return false;
                }
            })
            await loadImage(y,canvas)
        }
        index=index+1;
    }
    console.log(new Date().getTime())
}
function loadImage(y,cvs){
    return new Promise((resolve,reject) =>{
        var img = new Image();
        img.onload = function(){
            var w = img.width;
            var h = img.height;
            var ctx = cvs.getContext('2d');
            cvs.width = 200;
            cvs.height = 200;
            var ww = 200;
            var hh = 200;
            var h_=0;
            var w_=0;
            if(w<=ww&&h<=hh){
                h_=h;
                w_=w;
            }else{
                scale = Math.min(ww*0.99/w,hh*0.99/h);
                h_=h*scale;
                w_=w*scale;
            }
            ctx.drawImage(img,(ww-w_)/2,(hh-h_)/2,w_,h_);
            resolve(y.id);
        }
        img.src = y.content;
    });
}
function counter() {
  if ($('.show1.selected').length > 0)
  {
    btnshow();
    $('.send').addClass('selected');
  }
  else
  {
    btnhide();
    $('.send').removeClass('selected');
  }
  $('.send').attr('data-counter',$('.show1.selected').length);
}
function btnshow(){
    $('#download').show();
    $('#delete').show();
    $('#move').show();
    $('#restore').show();
    $('#ADD').show();
    $('#remove').show();
}
function btnhide(){
    $('#download').hide();
    $('#delete').hide();
    $('#move').hide();
    $('#restore').hide();
    $('#ADD').hide();
    $('#remove').hide();
}