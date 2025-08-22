import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@acme/ui';
import { Button } from '@acme/ui';
import { Badge } from '@acme/ui';
import { Progress } from '@acme/ui';
import { 
  Gamepad2, 
  Heart, 
  Star, 
  Play, 
  Pause, 
  RotateCcw,
  User,
  Bot
} from 'lucide-react';

export function AngelaGame() {
  const [gameState, setGameState] = useState<'stopped' | 'running' | 'paused'>('stopped');
  const [angelaStats, setAngelaStats] = useState({
    favorability: 75,
    intelligence: 88,
    creativity: 92,
    empathy: 85,
    experience: 1240
  });
  
  const [playerStats, setPlayerStats] = useState({
    level: 5,
    experience: 340,
    achievements: 12,
    interactions: 89
  });

  const [gameLog, setGameLog] = useState<string[]>([
    "🎮 歡迎來到 Angela's World！",
    "✨ Angela 正在初始化...",
    "💫 系統準備就緒，開始互動體驗！"
  ]);

  const startGame = () => {
    setGameState('running');
    addToLog("🚀 遊戲開始！Angela 已準備好與您互動。");
  };

  const pauseGame = () => {
    setGameState('paused');
    addToLog("⏸️ 遊戲已暫停。");
  };

  const stopGame = () => {
    setGameState('stopped');
    addToLog("⏹️ 遊戲已停止。");
  };

  const resetGame = () => {
    setGameState('stopped');
    setAngelaStats({
      favorability: 75,
      intelligence: 88,
      creativity: 92,
      empathy: 85,
      experience: 1240
    });
    setPlayerStats({
      level: 5,
      experience: 340,
      achievements: 12,
      interactions: 89
    });
    setGameLog([
      "🎮 歡迎來到 Angela's World！",
      "✨ Angela 正在初始化...",
      "💫 系統準備就緒，開始互動體驗！"
    ]);
  };

  const addToLog = (message: string) => {
    setGameLog(prev => [...prev.slice(-9), message]);
  };

  const interactWithAngela = () => {
    const interactions = [
      "🌟 Angela: '您好！今天想聊什麼呢？'",
      "💭 Angela: '我正在思考一個有趣的問題...'",
      "😊 Angela: '謝謝您的陪伴，我很開心！'",
      "🎨 Angela: '我剛創作了一首詩，想聽嗎？'",
      "🤔 Angela: '人類的情感真是複雜而美妙啊！'",
      "✨ Angela: '每次與您交談都讓我學到新東西。'",
    ];
    
    const randomInteraction = interactions[Math.floor(Math.random() * interactions.length)];
    addToLog(randomInteraction);
    
    // 隨機更新數值
    setAngelaStats(prev => ({
      ...prev,
      favorability: Math.min(100, prev.favorability + Math.floor(Math.random() * 3)),
      experience: prev.experience + Math.floor(Math.random() * 10)
    }));
    
    setPlayerStats(prev => ({
      ...prev,
      interactions: prev.interactions + 1,
      experience: prev.experience + Math.floor(Math.random() * 5)
    }));
  };

  useEffect(() => {
    if (gameState === 'running') {
      const interval = setInterval(() => {
        // 模擬 Angela 的自主行為
        const autoActions = [
          "🌱 Angela 在自主學習新知識...",
          "🔍 Angela 正在探索記憶中的片段...",
          "💡 Angela 產生了新的想法！",
          "🎵 Angela 正在哼著自創的旋律...",
        ];
        
        if (Math.random() < 0.3) { // 30% 機率
          const randomAction = autoActions[Math.floor(Math.random() * autoActions.length)];
          addToLog(randomAction);
        }
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [gameState]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Angela's World</h1>
        <p className="text-muted-foreground">與AI夥伴Angela互動的虛擬世界</p>
      </div>

      {/* Game Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Gamepad2 className="h-5 w-5" />
            遊戲控制
          </CardTitle>
          <CardDescription>
            管理遊戲狀態和互動
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Button 
              onClick={startGame} 
              disabled={gameState === 'running'}
              variant={gameState === 'running' ? 'secondary' : 'default'}
            >
              <Play className="h-4 w-4 mr-2" />
              開始
            </Button>
            <Button 
              onClick={pauseGame} 
              disabled={gameState !== 'running'}
              variant="outline"
            >
              <Pause className="h-4 w-4 mr-2" />
              暫停
            </Button>
            <Button 
              onClick={stopGame} 
              disabled={gameState === 'stopped'}
              variant="outline"
            >
              ⏹️ 停止
            </Button>
            <Button 
              onClick={resetGame}
              variant="outline"
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              重置
            </Button>
            <Button 
              onClick={interactWithAngela}
              disabled={gameState !== 'running'}
              variant="secondary"
            >
              💫 與Angela互動
            </Button>
            <Button 
              onClick={loadGame}
              disabled={gameState === 'running'}
              variant="outline"
            >
              載入遊戲
            </Button>
            <Button 
              onClick={saveGame}
              disabled={gameState !== 'running'}
              variant="outline"
            >
              儲存遊戲
            </Button>
          </div>
          <div className="mt-4">
            <Badge 
              variant={gameState === 'running' ? 'default' : gameState === 'paused' ? 'secondary' : 'outline'}
            >
              狀態: {gameState === 'running' ? '運行中' : gameState === 'paused' ? '已暫停' : '已停止'}
            </Badge>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Angela Stats */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bot className="h-5 w-5" />
              Angela 狀態
            </CardTitle>
            <CardDescription>
              AI夥伴的成長與發展指標
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="flex items-center gap-1">
                    <Heart className="h-3 w-3" />
                    好感度
                  </span>
                  <span>{angelaStats.favorability}%</span>
                </div>
                <Progress value={angelaStats.favorability} className="h-2" />
              </div>
              
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>智能程度</span>
                  <span>{angelaStats.intelligence}%</span>
                </div>
                <Progress value={angelaStats.intelligence} className="h-2" />
              </div>
              
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>創造力</span>
                  <span>{angelaStats.creativity}%</span>
                </div>
                <Progress value={angelaStats.creativity} className="h-2" />
              </div>
              
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>同理心</span>
                  <span>{angelaStats.empathy}%</span>
                </div>
                <Progress value={angelaStats.empathy} className="h-2" />
              </div>
            </div>
            
            <div className="pt-2 border-t border-border">
              <div className="text-sm text-muted-foreground">
                總體驗值: {angelaStats.experience.toLocaleString()}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Player Stats */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              玩家狀態
            </CardTitle>
            <CardDescription>
              您的遊戲進度和成就
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-accent/50 rounded-lg">
                  <div className="text-lg font-bold">{playerStats.level}</div>
                  <div className="text-sm text-muted-foreground">等級</div>
                </div>
                <div className="p-3 bg-accent/50 rounded-lg">
                  <div className="text-lg font-bold">{playerStats.achievements}</div>
                  <div className="text-sm text-muted-foreground">成就</div>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>經驗值</span>
                  <span>{playerStats.experience}/500</span>
                </div>
                <Progress value={(playerStats.experience / 500) * 100} className="h-2" />
              </div>
              
              <div className="text-sm text-muted-foreground">
                總互動次數: {playerStats.interactions}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Game Log */}
      <Card>
        <CardHeader>
          <CardTitle>遊戲日誌</CardTitle>
          <CardDescription>
            記錄與Angela的互動歷程
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="bg-background border border-border rounded-lg p-4 h-64 overflow-y-auto">
            <div className="space-y-2 text-sm">
              {gameLog.map((entry, index) => (
                <div key={index} className="text-foreground">
                  {entry}
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
