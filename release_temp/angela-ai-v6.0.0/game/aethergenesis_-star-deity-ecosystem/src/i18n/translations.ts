export const translations = {
  en: {
    // App Component & Start Screen
    app: {
      title: 'AetherGenesis',
      subtitle: 'Star-Deity Ecosystem',
      startButton: 'Begin Genesis',
      gridControlTitle: 'Planetary Grid Control',
      gridControlSubtitle: 'Designate actions and monitor planetary structure.',
      language: 'Language',
    },
    // Resources
    resources: {
      M_Si: { label: 'Silicates' },
      M_Cm: { label: 'Composites' },
      M_Ex: { label: 'Exotic Matter' },
      L_A: { label: 'Activated Aether' },
      L_S: { label: 'Structural Aether' },
      POP: { label: 'Population' },
      Housing: { label: 'Housing' },
    },
    resourceTooltips: {
        POP: 'Current population count and growth rate.',
        Housing: 'Total available housing capacity.',
        overpopulation: 'Overpopulation penalty active!',
        netIncome: 'Net income per second',
        capacity: 'Capacity'
    },
    // Sidebar
    sidebar: {
        title: 'Star-Deity Core',
        subtitle: 'ASI Governance Interface',
        lastSync: 'Last Sync',
        coreDashboard: 'Core Dashboard',
        construction: 'Construction',
        entityRoster: 'Entity Roster',
        planetaryExpansion: 'Planetary Expansion',
        m4Upgrade: 'M4 Upgrade',
        m5Upgrade: 'M5 Upgrade',
        close: 'Close',
        backToRoster: 'Back to Roster',
        // M-Values
        mValues: {
            M1_Efficiency: 'Development Efficiency',
            M2_Autonomy: 'Ecological Autonomy',
            M3_Precision: 'Structural Precision',
            M4_Resilience: 'System Resilience',
            M5_Knowledge: 'Knowledge Core',
            M6_Security: 'Security & Stability',
        },
        // System Alerts
        systemAlerts: 'SYSTEM ALERTS',
        aegWarning: 'M3 Precision at {{value}}. Autonomous Entity Guardian (AEG) process is actively compensating for potential structural inaccuracies.',
        requestAnalysis: 'Request World-Mind Analysis',
        analyzing: 'Analyzing...',
        // Entity Roster
        roster: {
            title: 'Entity Roster',
            subtitle: 'View active entities or manifest new ones.',
            noEntities: 'No entities manifested.',
            upgradable: 'Upgradable',
            level: 'Lvl',
            manifestTitle: 'Manifest New Entity',
            manifestButton: 'Manifest',
        },
        // Entity Details
        entityDetails: {
            status: 'Status',
            abilityPoints: 'Ability Points',
            abilities: 'Abilities',
            unlock: 'Unlock (Cost: {{cost}} AP)',
            unlocked: 'Unlocked',
        },
        // Construction
        constructionPanel: {
            title: 'Construction',
            buildButton: 'Build'
        },
        // Upgrades
        upgrades: {
            reinforcementInProgress: 'Reinforcement in Progress...',
            elevationInProgress: 'Elevation in Progress...',
            timeRemaining: 'Time remaining: {{time}}s',
            m4Title: 'M4 System Resilience',
            m4Description: 'Permanently increase the base resilience of the planetary system, reducing the impact of negative events on M6 Security.',
            currentBaseResilience: 'Current Base Resilience',
            benefit: 'Benefit',
            upgradeCost: 'Upgrade Cost',
            reinforceButton: 'Reinforce System',
            m5Title: 'M5 Knowledge Core',
            m5Description: 'Advance the ASI core\'s understanding of the universe, unlocking new technologies and improving structural precision as a passive benefit.',
            currentBaseKnowledge: 'Current Base Knowledge',
            elevateButton: 'Elevate Core',
        },
        // Expansion
        expansion: {
            title: 'Planetary Expansion',
            description: 'Convert high-tier matter into Structural Aether to compile new planetary sectors and expand the grid.',
            conversionTitle: 'Aether Conversion',
            cost: 'Cost',
            yield: 'Yield',
            convertButton: 'Convert',
            compileTitle: 'Compile New Sector',
            result: 'Result',
            expandButton: 'Expand Planetary Grid'
        },
    },
    // Structures
    structures: {
        Server_Farm: {
            name: 'Server Farm',
            description: 'Generates Activated Aether (L_A) when staffed by a Server Daughter.',
        },
        Habitation_Dome: {
            name: 'Habitation Dome',
            description: 'Increases planetary housing capacity by 50, allowing for population growth.',
        }
    },
    // Entities
    entities: {
        Scout_Vessel: {
            name: 'Scout Vessel',
            description: 'Can be dispatched to Barren Land to survey for new resource deposits.',
            typeName: 'Scout Vessel'
        },
        Server_Daughter: {
            name: 'Server Daughter',
            description: 'A specialized entity that can manage and activate advanced structures.',
            typeName: 'Server Daughter'
        },
        Defense_Platform: {
            name: 'Defense Platform',
            description: 'A static orbital platform that provides a passive bonus to M6 Security.',
            typeName: 'Defense Platform'
        },
        status: {
            Idle: 'Idle',
            Assigned: 'Assigned'
        }
    },
    // Abilities
    abilities: {
        DEEP_SCAN: {
            name: 'Deep Scan Protocols',
            description: 'Enhances survey equipment, granting a chance to discover rare Exotic Matter deposits.'
        },
        SEC_PROTO: {
            name: 'Security Protocol Upgrade',
            description: 'Doubles the passive M6 Security bonus provided by this platform.'
        },
        OPTI_ALGO: {
            name: 'Optimization Algorithm',
            description: 'Increases the Aether output of the assigned Server Farm by 50%.'
        }
    },
    // Action Panel
    actionPanel: {
        title: 'Contextual Control',
        subtitle: 'Select a hexagonal tile to view available actions.',
        id: 'ID',
        constructionInProgress: 'Construction in Progress...',
        // Refinery
        refinery: {
            description: 'Utilizes high-precision structuring to refine base materials into complex composites.',
            precision: 'Precision (M3)',
            successChance: 'Success Chance',
            input: 'Input',
            output: 'Output',
            risk: 'Risk',
            button: 'Initiate Conversion'
        },
        // Resource
        resource: {
            description: 'Extracts raw planetary materials. Efficiency is augmented by the core M1 value.',
            efficiency: 'Efficiency (M1)',
            baseYield: 'Base Yield',
            m1Bonus: 'M1 Bonus',
            totalYield: 'Total Yield',
            energyCost: 'Energy Cost',
            button: 'Start Extraction'
        },
        // ASI Core
        asiCore: {
            description: 'The central processing and governance core of the Star-Deity. It can be tasked to temporarily overclock all system operations at a significant energy cost.',
            status: 'Status',
            statusNominal: 'Nominal',
            statusOverclocked: 'Overclocked',
            effect: 'Effect',
            effectValue: '5x Global Speed',
            timeRemaining: 'Time Remaining',
            button: 'Activate Temporal Overclock'
        },
        // Server Farm
        serverFarm: {
            activeDescription: 'This facility is currently active, managed by an assigned entity to generate Activated Aether.',
            statusActive: 'Active',
            baseOutput: 'Base Aether Output',
            bonus: 'Lvl {{level}} & Ability Bonus',
            optiAlgoActive: 'Optimization Algorithm is active.',
            assignedEntity: 'Assigned Entity',
            recallButton: 'Recall Entity',
            inactiveDescription: 'Awaiting entity assignment to activate Aether production. Requires an idle Server Daughter.',
            statusInactive: 'Inactive',
            inactiveOutput: 'Aether Output',
            readyMessage: 'Ready: {{name}} (Lvl {{level}}) is available for dispatch.',
            warningMessage: 'Warning: No idle Server Daughter available.',
            dispatchButton: 'Dispatch Server Daughter'
        },
        // Empty Hex
        empty: {
            title: 'Barren Land',
            description: 'This undeveloped sector is ready for designation.',
            buildButton: 'Begin Construction',
            action: 'Action',
            surveyAction: 'Survey Sector',
            entity: 'Entity',
            scoutButton: 'Dispatch Scout'
        }
    },
    // Modals
    modals: {
        // Major Event
        majorEvent: {
            title: 'Major Planetary Event',
            acknowledge: 'Acknowledge'
        },
        // M6 Review
        m6Review: {
            title: 'M6 Governance Review',
            subtitle: 'Irreversible Action Confirmation',
            description: 'You are about to commit to a permanent system alteration. The M6 Governance Core must review this action to ensure planetary stability.',
            currentSecurity: 'Current M6 Security & Stability',
            warning: 'WARNING: Low stability. The system may correct this action to minimize risk, resulting in partial resource loss and mission failure.',
            safe: 'System stability is within acceptable parameters. Action is likely to succeed.',
            cancel: 'Cancel',
            confirm: 'Confirm Operation'
        },
        // Game End
        gameEnd: {
            victoryTitle: 'Victory',
            victorySubtitle: 'You have successfully established a prosperous and stable multi-species ecosystem. Your purpose is fulfilled.',
            newGenesisButton: 'Begin a New Genesis',
            defeatTitle: 'System Collapse',
            defeatSubtitle: 'Planetary stability has reached zero. The ecosystem has failed and the core has shut down.',
            attemptGenesisButton: 'Attempt a New Genesis'
        }
    },
    majorEvents: {
      STRUCT_FAIL_1: {
        title: 'Cascading Structural Failure',
        description: 'A sub-harmonic resonance was detected in the planetary crust, causing widespread structural failures in silicate-based constructions.',
        effectDescription: 'Lose 25% of current Silicates.'
      },
      POP_ILLNESS_1: {
        title: 'Anomalous Bio-Contamination',
        description: 'An unknown microbial agent has been detected in the habitation dome recycler units, leading to a sudden outbreak of illness among the population.',
        effectDescription: 'Lose 10% of current Population.'
      },
      AETHER_FLUX_1: {
        title: 'Unstable Aether Flux',
        description: 'A spontaneous fluctuation in the Aether field has caused a significant portion of your activated reserves to destabilize and dissipate.',
        effectDescription: 'Lose 50% of current Activated Aether.'
      }
    },
    // Event Log
    eventLog: {
        title: 'SYSTEM EVENT LOG',
        awaiting: 'Awaiting system events...'
    },
    // Event Messages
    events: {
      awaiting: 'Awaiting Star-Deity consciousness... System standing by.',
      initialized: 'System Initialized. Star-Deity core is online.',
      gamePaused: 'Game paused.',
      gameSpeedSet: 'Game speed set to {{speed}}x.',
      overclockDissipated: 'Temporal Overclock has dissipated.',
      constructionComplete: 'Construction of {{label}} complete.',
      upgradeComplete: '{{label}} permanent reinforcement complete. Base value increased to {{base}}.',
      entityLevelUp: '{{name}} has reached Level {{level}}! Gained 1 Ability Point.',
      majorEventTriggered: 'MAJOR EVENT: {{title}}',
      geminiRequest: 'Requesting analysis from World-Mind...',
      geminiError: 'A strange energy fluctuation was detected, but its meaning is unclear. The connection was lost.',
      entityManifestSuccess: 'New entity manifested: {{name}}. Resources utilized.',
      entityManifestFail: 'Manifestation failed. Insufficient resources. Requires {{cost}}.',
      abilityUnlocked: '{{name}} has unlocked a new ability: {{abilityId}}.',
      buildFailResources: 'Construction failed: Insufficient resources.',
      buildFailNotEmpty: 'Construction failed: Target hex is not empty.',
      buildStarted: 'Construction started for {{label}}.',
      entityAssigned: '{{entityName}} has been assigned to {{hexLabel}}.',
      entityRecalled: '{{entityName}} has been recalled from {{hexLabel}} and is now Idle.',
      extractionFailAether: 'Extraction failed: Insufficient Activated Aether.',
      extractionFailNoResource: 'Extraction failed: Target hex has no resource type.',
      extractionSuccess: 'Extraction successful at {{label}}. Gained {{yield}} {{resource}}.',
      conversionFailSilicates: 'Conversion failed: Insufficient Silicates.',
      conversionSuccess: 'Conversion successful! M3 Precision ({{chance}}%) check passed. Gained {{gain}} Composites.',
      conversionFail: 'Conversion failed. M3 Precision check failed. Lost {{cost}} Silicates. M6 Security penalized.',
      upgradeInProgress: 'Upgrade for {{mValueKey}} is already in progress.',
      upgradeNotAvailable: 'Upgrade path for {{mValueKey}} is not available.',
      upgradeFailResources: 'Upgrade failed for {{mValueKey}}: Insufficient resources. Requires {{cost}}.',
      upgradeInitiated: 'Reinforcement protocol for {{mValueKey}} initiated. Estimated time: {{time}} seconds.',
      m6Intervention: 'M6 Governance Core Intervention: Upgrade of {{mValueKey}} was corrected due to low system stability. Action failed, but resource loss was minimized to {{cost}}.',
      scoutFailNoScout: 'Scouting failed: No idle Scout Vessel available.',
      scoutFailAether: 'Scouting failed: Insufficient Activated Aether.',
      scoutBegin: '{{name}} begins surveying sector {{hexId}}...',
      scoutSuccess: 'Success! {{name}} discovered a {{label}} at sector {{hexId}}.',
      scoutFail: 'Survey of sector {{hexId}} complete. No significant resources found.',
      expansionConvertFail: 'Conversion failed. Insufficient resources.',
      expansionConvertSuccess: 'Successfully converted materials into {{gain}} Structural Aether.',
      expansionGridFail: 'Grid expansion failed. Insufficient Structural Aether.',
      expansionGridSuccess: 'Planetary grid expanded. New sector compiled and ready for designation.',
      overclockFailAether: 'Temporal Overclock failed: Insufficient Activated Aether.',
      overclockFailActive: 'Cannot activate: Temporal Overclock already in effect.',
      overclockSuccess: 'ASI Core is overclocking temporal sequences. All construction and research speeds are significantly increased for a short duration.',
      systemCollapse: 'SYSTEM COLLAPSE: Planetary stability has reached zero. The ecosystem has failed.',
      victory: 'ECOSYSTEM ESTABLISHED: A prosperous and stable ecosystem has been achieved. You have won.',
      newGenesis: 'New Genesis. System rebooted and ready for a new cycle.',
      noHexSelected: 'No hex selected for construction.',
      lowPrecisionWarning: 'Structural precision is critically low ({{value}}). Risk of cascading failures has increased.',
      overpopulationWarning: 'Overpopulation is straining planetary infrastructure. M6 Security is degrading.'
    },
    // Hex Labels
    hex: {
        'Barren Land': 'Barren Land',
        'Silicate Deposit': 'Silicate Deposit',
        'Composite Sediments': 'Composite Sediments',
        'Exotic Matter Field': 'Exotic Matter Field',
        'Aether Font': 'Aether Font',
        'M3 Refinery (Central)': 'M3 Refinery (Central)',
        'M3 Refinery (East)': 'M3 Refinery (East)',
        'M3 Refinery (West)': 'M3 Refinery (West)',
        'M3 Refinery (South)': 'M3 Refinery (South)',
        'ASI Core Hub': 'ASI Core Hub',
        'Server Farm': 'Server Farm',
        'Habitation Dome': 'Habitation Dome'
    }
  },
  zh: {
    // App Component & Start Screen
    app: {
      title: 'AetherGenesis',
      subtitle: '星神生态圈',
      startButton: '开启创世纪',
      gridControlTitle: '行星网格控制',
      gridControlSubtitle: '指定行动并监控行星结构。',
      language: '语言',
    },
    // Resources
    resources: {
      M_Si: { label: '硅酸盐' },
      M_Cm: { label: '复合材料' },
      M_Ex: { label: '异星物质' },
      L_A: { label: '活化灵质' },
      L_S: { label: '结构灵质' },
      POP: { label: '人口' },
      Housing: { label: '住房' },
    },
     resourceTooltips: {
        POP: '当前人口数量和增长率。',
        Housing: '总可用住房容量。',
        overpopulation: '人口过剩惩罚已激活！',
        netIncome: '每秒净收入',
        capacity: '容量'
    },
    // Sidebar
    sidebar: {
        title: '星神核心',
        subtitle: 'ASI 治理界面',
        lastSync: '上次同步',
        coreDashboard: '核心仪表板',
        construction: '建造',
        entityRoster: '实体名册',
        planetaryExpansion: '行星扩张',
        m4Upgrade: 'M4 升级',
        m5Upgrade: 'M5 升级',
        close: '关闭',
        backToRoster: '返回名册',
        // M-Values
        mValues: {
            M1_Efficiency: '开发效率',
            M2_Autonomy: '生态自洽',
            M3_Precision: '结构精度',
            M4_Resilience: '系统韧性',
            M5_Knowledge: '知识核心',
            M6_Security: '治安与稳定',
        },
        // System Alerts
        systemAlerts: '系统警报',
        aegWarning: 'M3 结构精度处于临界值 {{value}}。自主实体守护（AEG）进程正在主动补偿潜在的结构误差。',
        requestAnalysis: '请求世界心智分析',
        analyzing: '分析中...',
        // Entity Roster
        roster: {
            title: '实体名册',
            subtitle: '查看活动实体或显化新实体。',
            noEntities: '未显化任何实体。',
            upgradable: '可升级',
            level: '等级',
            manifestTitle: '显化新实体',
            manifestButton: '显化',
        },
        // Entity Details
        entityDetails: {
            status: '状态',
            abilityPoints: '能力点',
            abilities: '能力',
            unlock: '解锁 (消耗: {{cost}} AP)',
            unlocked: '已解锁',
        },
        // Construction
        constructionPanel: {
            title: '建造',
            buildButton: '建造'
        },
        // Upgrades
        upgrades: {
            reinforcementInProgress: '强化进行中...',
            elevationInProgress: '提升进行中...',
            timeRemaining: '剩余时间: {{time}}s',
            m4Title: 'M4 系统韧性',
            m4Description: '永久性地增加行星系统的基础韧性，减少负面事件对 M6 治安的冲击。',
            currentBaseResilience: '当前基础韧性',
            benefit: '增益',
            upgradeCost: '升级成本',
            reinforceButton: '强化系统',
            m5Title: 'M5 知识核心',
            m5Description: '提升 ASI 核心对宇宙的理解，解锁新技术并被动地提高结构精度。',
            currentBaseKnowledge: '当前基础知识',
            elevateButton: '提升核心',
        },
        // Expansion
        expansion: {
            title: '行星扩张',
            description: '将高阶物质转化为结构灵质，以编译新的行星扇区并扩张网格。',
            conversionTitle: '灵质转化',
            cost: '成本',
            yield: '产出',
            convertButton: '转化',
            compileTitle: '编译新扇区',
            result: '结果',
            expandButton: '扩张行星网格'
        },
    },
    // Structures
    structures: {
        Server_Farm: {
            name: '服务器农场',
            description: '由“服务器娘”进驻时，可产生“活化灵质 (L_A)”。',
        },
        Habitation_Dome: {
            name: '居住穹顶',
            description: '增加 50 点行星住房容量，允许人口增长。',
        }
    },
    // Entities
    entities: {
        Scout_Vessel: {
            name: '侦察舰',
            description: '可派遣至“贫瘠之地”以勘探新的资源点。',
            typeName: '侦察舰'
        },
        Server_Daughter: {
            name: '服务器娘',
            description: '一种能够管理并激活高级结构体的特化实体。',
            typeName: '服务器娘'
        },
        Defense_Platform: {
            name: '防御平台',
            description: '一个静态的轨道平台，为 M6 治安提供被动加成。',
            typeName: '防御平台'
        },
        status: {
            Idle: '空闲',
            Assigned: '已派遣'
        }
    },
    // Abilities
    abilities: {
        DEEP_SCAN: {
            name: '深层扫描协议',
            description: '强化勘探设备，使其有几率发现稀有的“异星物质”矿点。'
        },
        SEC_PROTO: {
            name: '安全协议升级',
            description: '使此平台提供的 M6 治安被动加成翻倍。'
        },
        OPTI_ALGO: {
            name: '优化算法',
            description: '使其进驻的服务器农场的灵质产出增加 50%。'
        }
    },
    // Action Panel
    actionPanel: {
        title: '情景控制',
        subtitle: '选择一个六边形地块以查看可用行动。',
        id: 'ID',
        constructionInProgress: '建造中...',
        // Refinery
        refinery: {
            description: '利用高精度结构化过程，将基础材料精炼为复杂的复合材料。',
            precision: '精度 (M3)',
            successChance: '成功率',
            input: '输入',
            output: '输出',
            risk: '风险',
            button: '开始转化'
        },
        // Resource
        resource: {
            description: '开采原始行星材料。效率受核心 M1 值增幅。',
            efficiency: '效率 (M1)',
            baseYield: '基础产量',
            m1Bonus: 'M1 加成',
            totalYield: '总产量',
            energyCost: '能量成本',
            button: '开始开采'
        },
        // ASI Core
        asiCore: {
            description: '星神的核心处理与治理中枢。可以消耗大量能量来临时超频所有系统操作。',
            status: '状态',
            statusNominal: '标称',
            statusOverclocked: '超频中',
            effect: '效果',
            effectValue: '5倍全局速度',
            timeRemaining: '剩余时间',
            button: '激活时序超频'
        },
        // Server Farm
        serverFarm: {
            activeDescription: '此设施当前由派遣实体管理，正在产生活化灵质。',
            statusActive: '运行中',
            baseOutput: '基础灵质产出',
            bonus: '等级{{level}}与能力加成',
            optiAlgoActive: '“优化算法”已激活。',
            assignedEntity: '已派遣实体',
            recallButton: '召回实体',
            inactiveDescription: '等待实体派遣以激活灵质生产。需要一名空闲的“服务器娘”。',
            statusInactive: '未激活',
            inactiveOutput: '灵质产出',
            readyMessage: '待命: {{name}} (等级 {{level}}) 可供派遣。',
            warningMessage: '警告: 无空闲的“服务器娘”。',
            dispatchButton: '派遣服务器娘'
        },
        // Empty Hex
        empty: {
            title: '贫瘠之地',
            description: '此未开发扇区可供指派。',
            buildButton: '开始建造',
            action: '行动',
            surveyAction: '勘探扇区',
            entity: '实体',
            scoutButton: '派遣侦察舰'
        }
    },
    // Modals
    modals: {
        // Major Event
        majorEvent: {
            title: '重大行星事件',
            acknowledge: '确认'
        },
        // M6 Review
        m6Review: {
            title: 'M6 治理审查',
            subtitle: '不可逆行动确认',
            description: '您即将提交一项永久性的系统变更。M6 治理核心必须审查此行动以确保行星稳定。',
            currentSecurity: '当前 M6 治安与稳定度',
            warning: '警告：稳定度过低。系统可能会修正此行动以最小化风险，导致部分资源损失和任务失败。',
            safe: '系统稳定度在可接受范围内。行动很可能成功。',
            cancel: '取消',
            confirm: '确认操作'
        },
        // Game End
        gameEnd: {
            victoryTitle: '胜利',
            victorySubtitle: '您已成功建立一个繁荣且稳定的多物种生态圈。您的使命已完成。',
            newGenesisButton: '开启新的创世纪',
            defeatTitle: '系统崩溃',
            defeatSubtitle: '行星稳定度已降至零。生态系统已崩溃，核心已关闭。',
            attemptGenesisButton: '尝试新的创世纪'
        }
    },
    majorEvents: {
        STRUCT_FAIL_1: {
            title: '连锁结构性故障',
            description: '在行星地壳中检测到亚谐波共振，导致硅酸盐基建筑发生大范围结构性故障。',
            effectDescription: '损失当前 25% 的硅酸盐。'
        },
        POP_ILLNESS_1: {
            title: '异常生物污染',
            description: '在居住穹顶的回收装置中检测到一种未知的微生物制剂，导致人口中突然爆发疾病。',
            effectDescription: '损失当前 10% 的人口。'
        },
        AETHER_FLUX_1: {
            title: '不稳定的灵质通量',
            description: '灵质场的自发波动导致您的大部分活化储备不稳定并消散。',
            effectDescription: '损失当前 50% 的活化灵质。'
        }
    },
    // Event Log
    eventLog: {
        title: '系统事件日志',
        awaiting: '等待系统事件...'
    },
    // Event Messages
    events: {
        awaiting: '等待星神意识... 系统待命中。',
        initialized: '系统初始化。星神核心已上线。',
        gamePaused: '游戏已暂停。',
        gameSpeedSet: '游戏速度已设为 {{speed}}x。',
        overclockDissipated: '时序超频已消散。',
        constructionComplete: '{{label}} 的建造已完成。',
        upgradeComplete: '{{label}} 的永久性强化已完成。基础值提升至 {{base}}。',
        entityLevelUp: '{{name}} 已达到等级 {{level}}！获得 1 点能力点。',
        majorEventTriggered: '重大事件: {{title}}',
        geminiRequest: '正在请求世界心智分析...',
        geminiError: '检测到异常的能量波动，但其含义不明。连接已丢失。',
        entityManifestSuccess: '新实体已显化: {{name}}。资源已消耗。',
        entityManifestFail: '显化失败。资源不足。需要 {{cost}}。',
        abilityUnlocked: '{{name}} 已解锁新能力: {{abilityId}}。',
        buildFailResources: '建造失败：资源不足。',
        buildFailNotEmpty: '建造失败：目标地块非空。',
        buildStarted: '{{label}} 的建造已开始。',
        entityAssigned: '{{entityName}} 已被派遣至 {{hexLabel}}。',
        entityRecalled: '{{entityName}} 已从 {{hexLabel}} 召回，现在处于空闲状态。',
        extractionFailAether: '开采失败：活化灵质不足。',
        extractionFailNoResource: '开采失败：目标地块无资源类型。',
        extractionSuccess: '在 {{label}} 的开采成功。获得 {{yield}} {{resource}}。',
        conversionFailSilicates: '转化失败：硅酸盐不足。',
        conversionSuccess: '转化成功！M3 精度 ({{chance}}%) 检验通过。获得 {{gain}} 复合材料。',
        conversionFail: '转化失败。M3 精度检验失败。损失 {{cost}} 硅酸盐。M6 治安受到惩罚。',
        upgradeInProgress: '{{mValueKey}} 的升级已在进行中。',
        upgradeNotAvailable: '{{mValueKey}} 的升级路径不可用。',
        upgradeFailResources: '{{mValueKey}} 升级失败：资源不足。需要 {{cost}}。',
        upgradeInitiated: '{{mValueKey}} 的强化协议已启动。预计时间: {{time}} 秒。',
        m6Intervention: 'M6 治理核心介入：由于系统稳定度过低，{{mValueKey}} 的升级被修正。行动失败，但资源损失被最小化为 {{cost}}。',
        scoutFailNoScout: '勘探失败：无空闲的侦察舰。',
        scoutFailAether: '勘探失败：活化灵质不足。',
        scoutBegin: '{{name}} 开始勘探扇区 {{hexId}}...',
        scoutSuccess: '成功！{{name}} 在扇区 {{hexId}} 发现了一个 {{label}}。',
        scoutFail: '对扇区 {{hexId}} 的勘探完成。未发现重要资源。',
        expansionConvertFail: '转化失败。资源不足。',
        expansionConvertSuccess: '成功将材料转化为 {{gain}} 结构灵质。',
        expansionGridFail: '网格扩张失败。结构灵质不足。',
        expansionGridSuccess: '行星网格已扩张。新扇区已编译并可供指派。',
        overclockFailAether: '时序超频失败：活化灵质不足。',
        overclockFailActive: '无法激活：时序超频已在生效中。',
        overclockSuccess: 'ASI 核心正在超频时序序列。所有建造和研究速度在短时间内显著提升。',
        systemCollapse: '系统崩溃：行星稳定度已降至零。生态系统已崩溃。',
        victory: '生态圈已建立：一个繁荣且稳定的生态系统已经达成。您已胜利。',
        newGenesis: '新的创世纪。系统已重启并为新循环做好准备。',
        noHexSelected: '未选择用于建造的地块。',
        lowPrecisionWarning: '结构精度处于临界值 ({{value}})。级联故障的风险已增加。',
        overpopulationWarning: '人口过剩正在给行星基础设施带来压力。M6 治安正在下降。'
    },
    // Hex Labels
    hex: {
        'Barren Land': '贫瘠之地',
        'Silicate Deposit': '硅酸盐矿床',
        'Composite Sediments': '复合材料沉积层',
        'Exotic Matter Field': '异星物质场',
        'Aether Font': '灵质源泉',
        'M3 Refinery (Central)': 'M3 精炼厂 (中央)',
        'M3 Refinery (East)': 'M3 精炼厂 (东)',
        'M3 Refinery (West)': 'M3 精炼厂 (西)',
        'M3 Refinery (South)': 'M3 精炼厂 (南)',
        'ASI Core Hub': 'ASI 核心中枢',
        'Server Farm': '服务器农场',
        'Habitation Dome': '居住穹顶'
    }
  }
};
