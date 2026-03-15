import { Scene } from 'phaser'
import type { RobotStatus, ChatSceneCallbacks } from '../types'

export class ChatScene extends Scene {
  private player!: Phaser.GameObjects.Container
  private npc!: Phaser.GameObjects.Container
  private playerDialog!: Phaser.GameObjects.Container
  private npcDialog!: Phaser.GameObjects.Container
  // callbacks 用于外部通信，当前通过直接调用方法实现
  // @ts-ignore - 保留以备后续扩展
  private callbacks: ChatSceneCallbacks | null = null
  private robotStatus: RobotStatus = 'idle'
  private typingTimer?: Phaser.Time.TimerEvent

  // 配置参数
  private readonly PLAYER_X = 200
  private readonly NPC_X = 600
  private readonly GROUND_Y = 400
  private readonly SCALE = 3

  constructor() {
    super({ key: 'ChatScene' })
  }

  setCallbacks(callbacks: ChatSceneCallbacks) {
    this.callbacks = callbacks
  }

  setRobotStatus(status: RobotStatus) {
    if (this.robotStatus === status) return
    this.robotStatus = status
    this.updateNPCAnimation()
  }

  preload() {
    // 创建像素风格的纹理（不依赖外部图片）
    this.createPixelTextures()
  }

  create() {
    // 创建背景
    this.createBackground()

    // 创建粒子效果
    // 创建角色
    this.createPlayer()
    this.createNPC()

    // 创建对话框（初始隐藏）
    this.createDialogs()

    // 启动待机动画
    this.updateNPCAnimation()

    // 初始入场动画
    this.playEntryAnimation()
  }

  // ========== 纹理创建 ==========

  private createPixelTextures() {
    // 玩家纹理（蓝色冒险者）
    const playerGraphics = this.make.graphics({ x: 0, y: 0 })
    // 身体
    playerGraphics.fillStyle(0x3498db)
    playerGraphics.fillRect(4, 8, 24, 16)
    // 头
    playerGraphics.fillStyle(0xffdbac)
    playerGraphics.fillRect(8, 0, 16, 8)
    // 眼睛
    playerGraphics.fillStyle(0x000000)
    playerGraphics.fillRect(10, 2, 4, 4)
    playerGraphics.fillRect(18, 2, 4, 4)
    // 腿
    playerGraphics.fillStyle(0x2c3e50)
    playerGraphics.fillRect(6, 24, 8, 8)
    playerGraphics.fillRect(18, 24, 8, 8)
    playerGraphics.generateTexture('player', 32, 32)

    // NPC 纹理（紫色机器人）
    const npcGraphics = this.make.graphics({ x: 0, y: 0 })
    // 身体
    npcGraphics.fillStyle(0x9b59b6)
    npcGraphics.fillRect(4, 6, 24, 18)
    // 头（圆形用矩形近似）
    npcGraphics.fillStyle(0x8e44ad)
    npcGraphics.fillRect(6, 0, 20, 8)
    // 眼睛（发光效果）
    npcGraphics.fillStyle(0x00ff88)
    npcGraphics.fillRect(8, 2, 6, 4)
    npcGraphics.fillRect(18, 2, 6, 4)
    // 天线
    npcGraphics.fillStyle(0x7d3c98)
    npcGraphics.fillRect(14, -6, 4, 6)
    npcGraphics.fillStyle(0xff0000)
    npcGraphics.fillRect(13, -8, 6, 4)
    npcGraphics.generateTexture('npc', 32, 32)

    // 对话框背景纹理
    const bubbleGraphics = this.make.graphics({ x: 0, y: 0 })
    bubbleGraphics.fillStyle(0xffffff)
    bubbleGraphics.fillRoundedRect(0, 0, 200, 80, 8)
    bubbleGraphics.lineStyle(3, 0x000000)
    bubbleGraphics.strokeRoundedRect(0, 0, 200, 80, 8)
    bubbleGraphics.generateTexture('bubble', 200, 80)

    // 地面纹理
    const groundGraphics = this.make.graphics({ x: 0, y: 0 })
    groundGraphics.fillStyle(0x27ae60)
    groundGraphics.fillRect(0, 0, 32, 32)
    // 草地细节
    groundGraphics.fillStyle(0x2ecc71)
    groundGraphics.fillRect(4, 4, 8, 8)
    groundGraphics.fillRect(20, 16, 6, 6)
    groundGraphics.generateTexture('ground', 32, 32)
  }

  // ========== 场景元素创建 ==========

  private createBackground() {
    // 渐变背景
    this.add.rectangle(
      this.cameras.main.width / 2,
      this.cameras.main.height / 2,
      this.cameras.main.width,
      this.cameras.main.height,
      0x2d3436
    )

    // 创建地板
    const tileCount = Math.ceil(this.cameras.main.width / 32) + 1
    for (let i = 0; i < tileCount; i++) {
      this.add.image(i * 32 + 16, this.GROUND_Y + 48, 'ground')
        .setOrigin(0.5)
        .setScale(1)
    }

    // 添加装饰性星星
    for (let i = 0; i < 20; i++) {
      const x = Phaser.Math.Between(50, this.cameras.main.width - 50)
      const y = Phaser.Math.Between(50, this.GROUND_Y - 100)
      const star = this.add.text(x, y, '✦', {
        fontSize: '16px',
        color: '#ffd700'
      }).setAlpha(Phaser.Math.FloatBetween(0.3, 0.8))

      // 星星闪烁动画
      this.tweens.add({
        targets: star,
        alpha: { from: star.alpha, to: star.alpha * 0.3 },
        duration: Phaser.Math.Between(1000, 3000),
        yoyo: true,
        repeat: -1,
        delay: Phaser.Math.Between(0, 2000)
      })
    }
  }

  // 粒子效果已移除，使用简单的视觉反馈

  private createPlayer() {
    this.player = this.add.container(this.PLAYER_X, this.GROUND_Y)

    // 身体精灵
    const body = this.add.sprite(0, 0, 'player')
      .setOrigin(0.5, 1)
      .setScale(this.SCALE)

    // 名字标签
    const nameTag = this.add.text(0, -100, '你', {
      fontFamily: '"Noto Sans SC", sans-serif',
      fontSize: '16px',
      color: '#ffffff',
      backgroundColor: '#3498db',
      padding: { x: 8, y: 4 }
    }).setOrigin(0.5)

    this.player.add([body, nameTag])

    // 待机动画（轻微上下浮动）
    this.tweens.add({
      targets: this.player,
      y: this.GROUND_Y - 5,
      duration: 2000,
      yoyo: true,
      repeat: -1,
      ease: 'Sine.easeInOut'
    })
  }

  private createNPC() {
    this.npc = this.add.container(this.NPC_X, this.GROUND_Y)

    // 身体精灵
    const body = this.add.sprite(0, 0, 'npc')
      .setOrigin(0.5, 1)
      .setScale(this.SCALE)

    // 名字标签
    const nameTag = this.add.text(0, -100, 'AI助手', {
      fontFamily: '"Noto Sans SC", sans-serif',
      fontSize: '16px',
      color: '#ffffff',
      backgroundColor: '#9b59b6',
      padding: { x: 8, y: 4 }
    }).setOrigin(0.5)

    this.npc.add([body, nameTag])

    // 添加发光效果（当激活时）
    const glow = this.add.ellipse(0, -48, 80, 20, 0x9b59b6, 0.3)
    glow.setName('glow')
    this.npc.addAt(glow, 0)
  }

  private createDialogs() {
    // 玩家对话框（左侧）
    this.playerDialog = this.createDialogContainer(
      this.PLAYER_X - 120,
      this.GROUND_Y - 180
    )

    // NPC 对话框（右侧）
    this.npcDialog = this.createDialogContainer(
      this.NPC_X + 120,
      this.GROUND_Y - 180
    )
  }

  private createDialogContainer(x: number, y: number): Phaser.GameObjects.Container {
    const container = this.add.container(x, y)
    container.setVisible(false)
    container.setScale(0)

    // 气泡背景
    const bg = this.add.image(0, 0, 'bubble').setOrigin(0.5)

    // 文本
    const text = this.add.text(0, -5, '', {
      fontFamily: '"Noto Sans SC", sans-serif',
      fontSize: '14px',
      color: '#000000',
      align: 'center',
      wordWrap: { width: 180 }
    }).setOrigin(0.5)

    // 指示箭头
    const arrow = this.add.triangle(
      0, 40, 0, 0, 10, 15, -10, 15,
      0xffffff
    )
    arrow.setStrokeStyle(2, 0x000000)

    container.add([bg, text, arrow])
    container.setData('text', text)

    return container
  }

  // ========== 动画控制 ==========

  private playEntryAnimation() {
    // 玩家从左侧进入
    this.player.x = -50
    this.tweens.add({
      targets: this.player,
      x: this.PLAYER_X,
      duration: 800,
      ease: 'Back.easeOut'
    })

    // NPC 从右侧进入
    this.npc.x = this.cameras.main.width + 50
    this.tweens.add({
      targets: this.npc,
      x: this.NPC_X,
      duration: 800,
      delay: 200,
      ease: 'Back.easeOut'
    })
  }

  private updateNPCAnimation() {
    const glow = this.npc.getByName('glow') as Phaser.GameObjects.Ellipse

    // 清除现有动画
    this.tweens.killTweensOf(this.npc)

    switch (this.robotStatus) {
      case 'idle':
        // 待机动画 - 轻微浮动
        this.tweens.add({
          targets: this.npc,
          y: this.GROUND_Y - 3,
          duration: 2000,
          yoyo: true,
          repeat: -1,
          ease: 'Sine.easeInOut'
        })
        glow.setAlpha(0.3)
        break

      case 'thinking':
        // 思考动画 - 摇晃 + 发光
        this.tweens.add({
          targets: this.npc,
          angle: { from: -5, to: 5 },
          duration: 200,
          yoyo: true,
          repeat: -1,
          ease: 'Sine.easeInOut'
        })
        this.tweens.add({
          targets: glow,
          alpha: { from: 0.3, to: 0.8 },
          scaleX: { from: 1, to: 1.3 },
          scaleY: { from: 1, to: 1.3 },
          duration: 500,
          yoyo: true,
          repeat: -1
        })
        break

      case 'speaking':
        // 说话动画 - 弹跳
        this.tweens.add({
          targets: this.npc,
          scaleY: { from: 1, to: 0.9 },
          scaleX: { from: 1, to: 1.05 },
          duration: 150,
          yoyo: true,
          repeat: -1
        })
        glow.setAlpha(0.6)
        break
    }
  }

  // ========== 对话功能 ==========

  showPlayerDialog(text: string) {
    this.showDialog(this.playerDialog, text, 0)
    this.playParticleEffect(this.PLAYER_X, this.GROUND_Y - 100)
  }

  showNPCDialog(text: string, onComplete?: () => void) {
    this.showTypingDialog(this.npcDialog, text, onComplete)
    this.playParticleEffect(this.NPC_X, this.GROUND_Y - 100)
  }

  private showDialog(
    container: Phaser.GameObjects.Container,
    text: string,
    delay: number = 0
  ) {
    const textObj = container.getData('text') as Phaser.GameObjects.Text
    textObj.setText(text)

    // 调整气泡大小
    const bounds = textObj.getBounds()
    const bubbleBg = container.first as Phaser.GameObjects.Image
    bubbleBg.setDisplaySize(Math.min(bounds.width + 40, 220), Math.min(bounds.height + 40, 120))

    container.setVisible(true)

    // 弹出动画
    this.tweens.add({
      targets: container,
      scale: { from: 0, to: 1 },
      duration: 300,
      delay,
      ease: 'Back.easeOut'
    })

    // 3秒后自动消失
    this.time.delayedCall(5000, () => {
      this.hideDialog(container)
    })
  }

  private showTypingDialog(
    container: Phaser.GameObjects.Container,
    text: string,
    onComplete?: () => void
  ) {
    // 清除之前的打字机效果
    if (this.typingTimer) {
      this.typingTimer.remove()
    }

    const textObj = container.getData('text') as Phaser.GameObjects.Text
    container.setVisible(true)

    // 调整气泡大小（预估）
    const bubbleBg = container.first as Phaser.GameObjects.Image
    bubbleBg.setDisplaySize(220, 100)

    // 打字机效果
    let index = 0
    const chars = text.split('')

    textObj.setText('')
    container.setScale(1)

    this.typingTimer = this.time.addEvent({
      delay: 30, // 每个字符 30ms
      callback: () => {
        if (index < chars.length) {
          textObj.setText(text.slice(0, index + 1))
          index++
        } else {
          this.typingTimer?.remove()
          onComplete?.()
        }
      },
      repeat: chars.length - 1
    })
  }

  private hideDialog(container: Phaser.GameObjects.Container) {
    this.tweens.add({
      targets: container,
      scale: 0,
      duration: 200,
      ease: 'Back.easeIn',
      onComplete: () => {
        container.setVisible(false)
      }
    })
  }

  private playParticleEffect(x: number, y: number) {
    // 简单的闪光效果代替粒子系统
    const flash = this.add.circle(x, y, 30, 0xffd700, 0.8)

    this.tweens.add({
      targets: flash,
      scale: { from: 0.5, to: 1.5 },
      alpha: { from: 0.8, to: 0 },
      duration: 500,
      ease: 'Power2',
      onComplete: () => {
        flash.destroy()
      }
    })

    // 添加一些闪烁的星星
    for (let i = 0; i < 5; i++) {
      const angle = (i / 5) * Math.PI * 2
      const starX = x + Math.cos(angle) * 40
      const starY = y + Math.sin(angle) * 40

      const star = this.add.text(starX, starY, '✨', {
        fontSize: '20px'
      }).setOrigin(0.5)

      this.tweens.add({
        targets: star,
        y: starY - 30,
        alpha: { from: 1, to: 0 },
        scale: { from: 1, to: 0.5 },
        duration: 600,
        delay: i * 50,
        onComplete: () => {
          star.destroy()
        }
      })
    }
  }
}
