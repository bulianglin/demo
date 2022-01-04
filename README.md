# demo

## 01 <https://youtu.be/VONkHvKkCX0>
## 松鼠VPN节点提取相关文件 视频被下架，备份：<https://bulianglin.com/g/songsu/>
## nodesCatch视频教程 <https://youtu.be/aSR6OuqtFdU>
## 不良林 VPN <https://youtu.be/HuyPaM41ytA>
## EasyClash <https://youtu.be/-I5T1G6NdKM> <https://youtu.be/1Xn-tRosThs>
## nodesCatch V2.0视频教程 <https://youtu.be/fHJDvJIptts>

### nodesCatch V2.0目前已知问题：
1、有效节点变无效：一般是vmess节点，导入节点使用的是subconverter进行节点格式转换，但是windows版的subconverter有个bug，转换clash后会将vmess节点的aid参数丢失，如果你是直接粘贴clash配置文件到节点列表，可能会导致本来可以使用的vmess节点测速显示无效，目前的解决方法是直接粘贴url格式的节点到节点列表再测速，剩下的只有等工具作者修复

2、无法导入节点：和clash.net有冲突，因为clash.net也内置了subconverter，解决方法是直接删掉测速软件目录里的subconverter目录，但是这样的话在使用测速软件时就必须运行clash.net。或者先退出clash.net再测速

3、切换测速配置文件失败：clash内核不允许 h2/grpc 的节点tls为false，解决方法是将传输协议为h2或者grpc的节点删除或者使用Xray内核测速
