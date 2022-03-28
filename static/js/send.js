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
              window.location.reload();
          }
      })
}
function operateAblum(e,url,t,event){
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
          data:JSON.stringify({'id_list':a,'ablumName':event.target.innerText}),
          contentType:'application/json',
          success:function(data){
              alert(data);
          }
      })
  }else if(t == 'remove'){
      $.ajax({
          type:'POST',
          url:url,
          processData:false,
          contentType:false,
          data:JSON.stringify({'id_list':a,'ablumName':event}),
          contentType:'application/json',
          success:function(data){
              alert(data);
              window.location.reload();
          }
      })
  }
}
function AlbumRename(name1,name2,url)
{
    $.ajax({
          type:'POST',
          url:url,
          processData:false,
          contentType:false,
          data:JSON.stringify({'ablumName1':name1,'ablumName2':name2}),
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

