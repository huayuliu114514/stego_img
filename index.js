// index.js
const defaultAvatarUrl = 'https://mmbiz.qpic.cn/mmbiz/icTdbqWNOwNRna42FI242Lcia07jQodd2FJGIYQfG0LAJGFxM4FbnQP6yfMxBgJ0F3YRqJCJ1aPAK2dQagdusBZg/0'


Page({

  data: {
    previewImageUrl: '' 
  },

  // 点击“拍照并上传”按钮时触发
  takePhoto() {
 
    const cameraCtx = wx.createCameraContext()

    cameraCtx.takePhoto({
      quality: 'high', 
      success: (res) => {

        this.setData({
          previewImageUrl: res.tempImagePath 
        })

        this.convertToJPEG(res.tempImagePath)
      }
    })
  },

  // 将拍摄的照片转为JPEG格式（统一上传格式）
  convertToJPEG(tempImagePath) {
    const canvasCtx = wx.createCanvasContext('myCanvas')
    canvasCtx.drawImage(tempImagePath, 0, 0, 300, 300)
    canvasCtx.draw(false, () => {
      wx.canvasToTempFilePath({
        canvasId: 'myCanvas', 
        fileType: 'jpg', 
        quality: 0.8, 
        success: (res) => {
          this.uploadImage(res.tempFilePath)
        }
      })
    })
  },

  // 把JPEG图片上传到后端接口
  uploadImage(filePath) {
    wx.uploadFile({
      url: 'http://p6296a26.natappfree.cc/upload', // 后续替换为后端提供的接口地址
      filePath: filePath, // 要上传的JPEG图片临时路径
      name: 'file', // 后端接收文件的字段名（需和后端一致）
      success: (res) => {
        const result = JSON.parse(res.data)
        if (result.status) {
          wx.showToast({ title: '上传成功', icon: 'success' })
        } else {
          wx.showToast({ title: '上传失败', icon: 'none' })
        }
      },
      fail: (err) => {
        wx.showToast({ title: '网络错误', icon: 'none' })
        console.error('上传失败：', err)
      }
    })
  }
})