const fs = require('fs');
let content = fs.readFileSync('game-data/cards.js', 'utf8');

let fixes = 0;

// === FIX CATEGORIES ===
const catMap = {
  '草藥':'herb','木柄':'material','鐵礦':'material','火元素':'element',
  '鐵錠':'material','皮革':'material','絲線':'material','空瓶':'material',
  '小石頭':'material','黏土':'material','魔法粉':'material','靈木':'material',
  '水晶碎片':'material','布料':'material','龍鱗':'material','生鏽釘子':'material',
  '樹枝':'material','羽毛':'material','貝殼':'material','乾燥花':'material',
  '蠟燭頭':'material','麻繩':'material','碎陶瓷':'material','破布':'material',
  '松果':'material','彩色玻璃片':'material','炭筆':'material','木雕':'material',
  '毒針':'material',
  '鐵劍':'weapon','鋼刀':'weapon','匕首':'weapon','水晶法杖':'weapon',
  '木杖':'weapon','長弓':'weapon',
  '皮甲':'armor','鐵甲':'armor','斗篷':'armor','皮帽':'armor',
  '鐵盔':'armor','草鞋':'armor','鐵靴':'armor','盾牌':'armor',
  '護身符':'accessory','戒指':'accessory','手鐲':'accessory',
  '腰帶':'accessory','項鍊':'accessory','幸運幣':'accessory',
  '火焰藥水':'consumable','治療藥水':'consumable','魔力藥水':'consumable',
  '解毒草':'consumable','靈力藥':'consumable','濃縮藥水':'consumable',
  '生命果':'consumable','乾糧':'consumable','提神茶':'consumable','繃帶':'consumable',
  '古老鑰匙':'key','神秘地圖':'document','書信':'document',
  '記憶水晶':'magic','古代硬幣':'currency','古代硬貨':'currency',
  '舊鑰匙圈':'trinket','修復服務':'service',
};

for (const [name, cat] of Object.entries(catMap)) {
  const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  // Match: name: 'X',\n      desc: (no category in between)
  const re = new RegExp(`(name: '${escaped}',\\n)(\\s*)(desc:)`, 'g');
  const newContent = content.replace(re, `$1$2category: '${cat}',\n$2$3`);
  if (newContent !== content) {
    fixes++;
    content = newContent;
  }
}

console.log('Category fixes:', fixes);

// === FIX ENEMY DESCRIPTIONS (short ones) ===
const enemyDescs = {
  '野狼': '森林邊緣的飢餓野狼。眼睛在黑暗中閃爍，低聲咆哮。',
  '哥布林': '矮小的綠色生物。喜歡偷東西，被發現就跑。膽小但成群時很危險。',
  '石像鬼': '古老的石像鬼。白天是雕像，夜晚甦醒巡邏遺跡。',
  '暗影靈': '飄忽的暗影生物。觸碰它會讓你感到一陣寒意，然後忘記一些事情。',
  '廢鐵傀儡': '鏽蝕的機械傀儡。仍在執行早已過期的指令，對所有移動目標敵意。',
  '晶石蜘蛛': '身體由半透明結晶構成的蜘蛛。蛛絲堅韌如鋼線。',
  '盜賊': '鬼祟的人形盜賊。在陰影中移動，專門偷取旅人的補給。',
  '蛇妖': '下半身是蛇尾的妖物。有毒牙，被咬會麻痹。',
  '幽靈': '無實體的怨靈。無法用物理攻擊傷害，只能驅散。',
  '巨熊': '龐大的棕熊。被激怒時力量驚人，能拍碎樹木。',
  '元素核心': '凝聚的元素能量體。沒有固定形態，不斷變化。',
  '古代守衛': '古代遺跡的守衛。由石材和金屬構成，千年未朽。',
  '火靈': '火焰凝聚的精靈。靠近它空氣會扭曲。',
  '水靈': '水之精靈。流動不定，能治癒也能溺斃。',
  '風靈': '風之精靈。幾乎看不見，只聽得到呼嘯聲。',
  '地靈': '大地之靈。沉重、緩慢，但一擊能裂開岩石。',
  '光靈': '光之精靈。刺眼的光芒讓你無法直視。',
  '暗靈': '暗之精靈。吞噬光線，你會迷失方向。',
  '雷靈': '雷電之精靈。劈啪作響，空氣中充滿臭氧味。',
  '冰靈': '冰霜之精靈。周圍的水會結冰，呼吸可見白霧。',
  '森靈': '森林之靈。由藤蔓和樹葉構成，移動時枝葉沙沙作響。',
  '星靈': '星辰之靈。身體由微小的光點組成，像行走的星空。',
};

let efixes = 0;
for (const [name, desc] of Object.entries(enemyDescs)) {
  const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  // Match short desc after this enemy name
  const re = new RegExp(`(name: '${escaped}',\\n\\s*)(desc: ')([^']{3,24})(')`, 'g');
  const newContent = content.replace(re, `$1$2${desc}$4`);
  if (newContent !== content) {
    efixes++;
    content = newContent;
  }
}

console.log('Enemy desc fixes:', efixes);

// === FIX ITEM DESCRIPTIONS (placeholder ones) ===
const itemDescs = {
  '草藥': '生長在河邊的常見藥草。揉碎後有淡淡的草香。',
  '木柄': '堅硬的木頭握柄。經過打磨，握感舒適。',
  '鐵礦': '未經熔煉的鐵礦石。表面有金屬光澤，需要高溫才能加工。',
  '火元素': '凝聚的火焰碎片。觸摸會感到溫熱，但不會灼傷。',
  '鐵錠': '熔煉後的純鐵錠。沉重、堅硬，是鍛造的基礎材料。',
  '皮革': '處理過的動物皮革。柔韌耐用，適合製作輕型防具。',
  '絲線': '堅韌的絲線。細但不容易斷，可以編織或縫合。',
  '空瓶': '乾淨的空玻璃瓶。可以用來裝藥水或其他液體。',
  '小石頭': '光滑的小石頭。握在手裡有點沉，可以當作投擲武器。',
  '黏土': '潮濕的黏土。有可塑性，可以塑形後燒製成器皿。',
  '魔法粉': '散發微光的粉末。是施法的催化劑，能增強咒語效果。',
  '靈木': '在迴廊附近生長的樹木。木質堅硬，帶有微弱的藍色光芒。',
  '水晶碎片': '破碎的水晶。仍殘留著微弱的能量，握在手裡會微微發熱。',
  '布料': '普通的布料。可以用來製作輕型防具或修補衣物。',
  '龍鱗': '從龍身上脫落的鱗片。堅硬無比，折射出彩虹色的光。',
  '生鏽釘子': '從廢墟中撿到的釘子。鏽跡斑斑但還能用。',
  '毒針': '從毒蜘蛛身上取下的針。尖端帶有微量毒素。',
  '古代硬幣': '鏽蝕的古代硬幣。上面的圖案已經模糊不清。',
  '古代硬貨': '古老的貨幣。金屬表面已被氧化，但仍有收藏價值。',
  '樹枝': '撿來的樹枝。可以用作簡易的武器或燃料。',
  '羽毛': '柔軟的羽毛。可能是某種鳥類留下的。',
  '貝殼': '光滑的貝殼。放在耳邊能聽到微弱的海浪聲。',
  '乾燥花': '壓乾的花朵。顏色褪了不少，但還能辨認。',
  '蠟燭頭': '燃燒過的蠟燭。只剩一小截，但還能點亮。',
  '麻繩': '粗糙的麻繩。結實耐用，可以用來綁東西。',
  '碎陶瓷': '破碎的陶瓷碎片。邊緣鋒利，小心割手。',
  '破布': '破舊的布片。可以當作燃料或用來擦拭。',
  '松果': '從松樹上掉下來的松果。可以當作引火物。',
  '彩色玻璃片': '彩色的玻璃碎片。陽光穿過會投射出彩色光斑。',
  '炭筆': '書寫用的炭筆。可以用來做記號。',
  '木雕': '手工雕刻的小木雕。造型是不知名的小動物。',
  '鐵劍': '用鐵錠鍛造的劍。比木棍強得多。',
  '鋼刀': '經過多次鍛打的鋼刀。刃口鋒利。',
  '匕首': '短小的匕首。適合近身搏鬥。',
  '水晶法杖': '鑲嵌水晶的法杖。能增幅魔法威力。',
  '木杖': '簡單的木杖。可以用來行走或防身。',
  '長弓': '射程遠的長弓。需要一定力氣才能拉開。',
  '皮甲': '用皮革製成的輕型護甲。不影響活動。',
  '鐵甲': '沉重但堅固的鐵甲。能擋住大部分攻擊。',
  '斗篷': '用布料製成的斗篷。輕便，能遮風擋雨。',
  '皮帽': '皮革製成的頭盔。保護頭部免受輕微傷害。',
  '鐵盔': '沉重的鐵製頭盔。防護力強但視野受限。',
  '草鞋': '用草編織的鞋子。輕便但不耐磨。',
  '鐵靴': '沉重的鐵靴。走路聲音很大。',
  '盾牌': '木製盾牌。可以格擋攻擊。',
  '護身符': '刻有符文的護身符。據說能驅邪。',
  '戒指': '金屬戒指。戴上後感覺指尖微微發熱。',
  '手鐲': '雕刻精美的手鐲。可能有某種用途。',
  '腰帶': '皮製腰帶。可以掛上小物品。',
  '項鍊': '串著寶石的項鍊。寶石在暗處會發光。',
  '幸運幣': '據說帶來幸運的硬幣。不知道是不是真的。',
  '古老鑰匙': '外觀古老的鑰匙。不知道能開什麼鎖。',
  '神秘地圖': '標記不明的地圖。有些位置用未知符號標記。',
  '書信': '一封已經拆開的信。字跡潦草。',
  '記憶水晶': '能儲存記憶的水晶。觸摸能看到片段畫面。',
  '舊鑰匙圈': '串著幾把小鑰匙的鑰匙圈。用途不明。',
  '火焰藥水': '裝著液態火焰的瓶子。擰開瓶蓋能感到熱氣。',
  '治療藥水': '紅色的液體。喝下去傷口會癒合，但味道很苦。',
  '魔力藥水': '藍色的魔法藥水。能恢復施法所需的精力。',
  '解毒草': '搗碎的解毒草。可以中和大多數毒素。',
  '靈力藥': '用靈木提煉的藥水。能暫時增強感知力。',
  '濃縮藥水': '多種藥水的混合物。效果強烈但不穩定。',
  '生命果': '傳說中的果實。能大幅恢復體力。',
  '乾糧': '方便攜帶的乾糧。味道一般但能填飽肚子。',
  '提神茶': '泡開後香氣撲鼻。能消除疲勞。',
  '繃帶': '醫用繃帶。可以止血和固定傷口。',
  '修復服務': '修復受損裝備的服務。品質取決於工匠。',
};

// Generic placeholder patterns to match
const placeholderPatterns = [
  '可用於合成', '武器握柄材料', '未熔煉的鐵礦石', '凝聚的火元素碎片',
  '熔煉後的鐵錠', '處理過的動物皮革', '堅韌的絲線', '乾淨的空玻璃瓶',
  '光滑的小石頭', '潮濕的黏土', '散發微光的粉末', '在迴廊附近生長',
  '破碎的水晶', '普通的布料', '從龍身上脫落的鱗片', '從廢墟中撿到',
];

let ifixes = 0;
for (const [name, desc] of Object.entries(itemDescs)) {
  const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  // Match desc after this item name, only if it's a placeholder
  for (const ph of placeholderPatterns) {
    const phEsc = ph.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const re = new RegExp(`(name: '${escaped}',\\n\\s*[^\\n]*?desc: ')${phEsc}(')`, 'g');
    const newContent = content.replace(re, `$1${desc}$2`);
    if (newContent !== content) {
      ifixes++;
      content = newContent;
      break; // Only fix first match per item name
    }
  }
}

console.log('Item desc fixes:', ifixes);
console.log('Total:', fixes + efixes + ifixes);

fs.writeFileSync('game-data/cards.js', content, 'utf8');
