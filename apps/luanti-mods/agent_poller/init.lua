-- Angela AI Polling Bridge Mod (Server-side)
-- Polls Python bridge via async HTTP fetch, executes returned actions.

local http_api = minetest.request_http_api()

if not http_api then
    minetest.log("error", "[agent_poller] HTTP API not available!")
    return
end

local BRIDGE_URL = "http://192.168.1.112:30003"
local TARGET_PLAYER_NAME = "AngelaBot"
local POLL_INTERVAL = 2.0
local last_poll = 0
-- Test-only item grants. Default OFF: enable with
-- `agent_poller_allow_give = true` in minetest.conf for manual verification.
local ALLOW_GIVE = minetest.settings:get_bool("agent_poller_allow_give", false)

local function get_target_player()
    local players = minetest.get_connected_players()
    for _, player in ipairs(players) do
        if player:get_player_name() == TARGET_PLAYER_NAME then
            return player
        end
    end
    if #players > 0 then
        return players[1]
    end
    return nil
end

-- Short recipe ids (as sent by the agent) to Minetest Game items.
-- Mirrors apps/backend/src/ai/multimodal/game_memory_bridge.py defaults.
-- NOTE: must be defined BEFORE execute_commands (Lua locals are only
-- visible after their declaration point in the chunk).
local RECIPES = {
    stick = {needs = {wood = 2}, gives = {stick = 4}},
    wooden_pickaxe = {needs = {wood = 3}, gives = {wooden_pickaxe = 1}},
    stone_pickaxe = {needs = {cobblestone = 3, stick = 2}, gives = {stone_pickaxe = 1}},
    stone_axe = {needs = {cobblestone = 3, stick = 2}, gives = {stone_axe = 1}},
    stone_shovel = {needs = {cobblestone = 1, stick = 2}, gives = {stone_shovel = 1}},
    stone_sword = {needs = {cobblestone = 2, stick = 1}, gives = {stone_sword = 1}},
    furnace = {needs = {cobblestone = 8}, gives = {furnace = 1}},
    chest = {needs = {wood = 8}, gives = {chest = 1}},
    crafting_table = {needs = {wood = 4}, gives = {crafting_table = 1}},
    torch = {needs = {stick = 1, coal = 1}, gives = {torch = 4}},
}

-- Short names to Minetest Game itemstrings.
local ITEMS = {
    wood = "default:wood",
    cobblestone = "default:cobble",
    stick = "default:stick",
    coal = "default:coal_lump",
    wooden_pickaxe = "default:pick_wood",
    stone_pickaxe = "default:pick_stone",
    stone_axe = "default:axe_stone",
    stone_shovel = "default:shovel_stone",
    stone_sword = "default:sword_stone",
    furnace = "default:furnace",
    chest = "default:chest",
    crafting_table = "default:workbench",
    torch = "default:torch",
}

local function count_item(inv, itemstring)
    local total = 0
    for i = 1, inv:get_size("main") do
        local stack = inv:get_stack("main", i)
        if not stack:is_empty() and stack:get_name() == itemstring then
            total = total + stack:get_count()
        end
    end
    return total
end

local function do_craft(player, action)
    local recipe_id = action.recipe_id or action.recipe or "auto"
    local recipe = RECIPES[recipe_id]
    if not recipe then
        -- Auto: pick the first recipe whose ingredients are all present
        for rid, r in pairs(RECIPES) do
            local ok = true
            local inv = player:get_inventory()
            for short, n in pairs(r.needs) do
                if count_item(inv, ITEMS[short] or short) < n then
                    ok = false
                    break
                end
            end
            if ok then
                recipe_id = rid
                recipe = r
                break
            end
        end
    end
    if not recipe then
        minetest.log("action", "[agent_poller] craft failed (no recipe): " .. tostring(action.recipe_id))
        return
    end
    local inv = player:get_inventory()
    for short, n in pairs(recipe.needs) do
        local itemstring = ITEMS[short] or short
        if count_item(inv, itemstring) < n then
            minetest.log(
                "action",
                "[agent_poller] craft failed (missing "
                    .. itemstring
                    .. ") for "
                    .. player:get_player_name()
            )
            return
        end
    end
    for short, n in pairs(recipe.needs) do
        local itemstring = ITEMS[short] or short
        local rest = n
        for i = 1, inv:get_size("main") do
            if rest <= 0 then
                break
            end
            local stack = inv:get_stack("main", i)
            if not stack:is_empty() and stack:get_name() == itemstring then
                local take = math.min(rest, stack:get_count())
                stack:set_count(stack:get_count() - take)
                inv:set_stack("main", i, stack)
                rest = rest - take
            end
        end
    end
    for short, n in pairs(recipe.gives) do
        inv:add_item("main", (ITEMS[short] or short) .. " " .. n)
    end
    minetest.log(
        "action",
        "[agent_poller] crafted " .. recipe_id .. " for " .. player:get_player_name()
    )
end

local function execute_commands(actions, player)
    if not player or not actions then
        return
    end
    for _, action in ipairs(actions) do
        if action.type == "move" then
            local yaw = player:get_look_horizontal()
            local dir = vector.new(action.forward or 0, 0, action.strafe or 0)
            dir = vector.rotate(dir, vector.new(0, yaw, 0))
            player:set_velocity(vector.multiply(dir, 4))
            if action.jump then
                local v = player:get_velocity()
                player:set_velocity({x = v.x, y = 6, z = v.z})
            end
            -- Server-side step: Luanti movement is client-authoritative, so
            -- set_velocity alone never displaces a standing-still client
            -- (800 move actions, 0.0m gained — measured). Step the position
            -- directly, collision-aware, so move decisions become motion.
            local flat = vector.new(dir.x, 0, dir.z)
            if vector.length(flat) > 0.05 then
                flat = vector.normalize(flat)
                local pos = player:get_pos()
                local stepped = false
                for _, dy in ipairs({0, 1}) do
                    local dest = vector.add(
                        vector.add(pos, vector.multiply(flat, 1.5)),
                        {x = 0, y = dy, z = 0}
                    )
                    local feet = minetest.get_node(dest)
                    local head = minetest.get_node(vector.add(dest, {x = 0, y = 1, z = 0}))
                    local fdef = minetest.registered_nodes[feet.name] or {}
                    local hdef = minetest.registered_nodes[head.name] or {}
                    if not fdef.walkable and not hdef.walkable then
                        player:set_pos(dest)
                        minetest.log(
                            "action",
                            "[agent_poller] moved to "
                                .. minetest.pos_to_string(dest, 1)
                                .. " for "
                                .. player:get_player_name()
                        )
                        stepped = true
                        break
                    end
                end
                if not stepped then
                    minetest.log(
                        "action",
                        "[agent_poller] move blocked (wall) for " .. player:get_player_name()
                    )
                end
            end
        elseif action.type == "look" then
            local yaw = (action.yaw_delta or 0) + player:get_look_horizontal()
            local pitch = (action.pitch_delta or 0) + player:get_look_vertical()
            player:set_look_horizontal(yaw)
            player:set_look_vertical(math.max(-math.pi / 2, math.min(math.pi / 2, pitch)))
        elseif action.type == "dig" then
            local pos = player:get_pos()
            local dir = player:get_look_dir()
            local target = vector.add(pos, vector.multiply(dir, 4))
            local node = minetest.get_node(target)
            if node.name ~= "air" then
                minetest.node_dig(target, node, player)
                minetest.log("action", "[agent_poller] dig executed for " .. player:get_player_name())
            end
        elseif action.type == "place" then
            local pos = player:get_pos()
            local dir = player:get_look_dir()
            local pname = player:get_player_name()
            -- Candidates: look target first, then nearby cells. The agent has
            -- no vision, so look-aim is luck; fall back to the first free
            -- cell with solid support to guarantee progress.
            local candidates = {
                vector.round(vector.add(pos, vector.multiply(dir, 3))),
            }
            for _, off in ipairs({
                {x = 0, y = 2, z = 0},
                {x = 1, y = 1, z = 0},
                {x = -1, y = 1, z = 0},
                {x = 0, y = 1, z = 1},
                {x = 0, y = 1, z = -1},
                {x = 1, y = 0, z = 0},
                {x = -1, y = 0, z = 0},
                {x = 0, y = 0, z = 1},
                {x = 0, y = 0, z = -1},
            }) do
                candidates[#candidates + 1] = vector.round(vector.add(pos, off))
            end
            local target = nil
            local under = nil
            for _, c in ipairs(candidates) do
                if minetest.get_node(c).name == "air" then
                    local below = vector.add(c, {x = 0, y = -1, z = 0})
                    if minetest.get_node(below).name ~= "air" then
                        target = c
                        under = below
                        break
                    end
                end
            end
            if not target then
                minetest.log("action", "[agent_poller] place failed (no free cell) for " .. pname)
            else
                local stack = player:get_wielded_item()
                if stack:is_empty() or not minetest.registered_nodes[stack:get_name()] then
                    -- Agent has no select-slot action: auto-wield the first
                    -- placeable node stack so place works autonomously.
                    local inv = player:get_inventory()
                    local found = false
                    for i = 1, inv:get_size("main") do
                        local s = inv:get_stack("main", i)
                        if not s:is_empty() and minetest.registered_nodes[s:get_name()] then
                            player:set_wield_index(i)
                            stack = player:get_wielded_item()
                            found = true
                            break
                        end
                    end
                    if not found then
                        stack = ItemStack("")
                    end
                end
                if stack:is_empty() then
                    minetest.log("action", "[agent_poller] place failed (nothing placeable) for " .. pname)
                else
                    -- under/above were resolved in the candidate scan above.
                    local leftover = minetest.item_place(
                        stack,
                        player,
                        {type = "node", under = under, above = target}
                    )
                    if leftover then
                        player:set_wielded_item(leftover)
                    end
                    minetest.log(
                        "action",
                        "[agent_poller] placed "
                            .. stack:get_name()
                            .. " at "
                            .. minetest.pos_to_string(target)
                            .. " for "
                            .. pname
                    )
                end
            end
        elseif action.type == "chat" then
            minetest.chat_send_all("[Angela] " .. tostring(action.message or ""))
        elseif action.type == "craft" then
            do_craft(player, action)
        elseif action.type == "give" then
            -- TEST ONLY, gated by agent_poller_allow_give (default false).
            if not ALLOW_GIVE then
                minetest.log("warning", "[agent_poller] give rejected (allow_give off)")
            else
            local itemstring = ITEMS[action.item] or action.item
            local count = tonumber(action.count) or 1
            if itemstring then
                player:get_inventory():add_item("main", itemstring .. " " .. count)
                minetest.log(
                    "action",
                    "[agent_poller] gave " .. itemstring .. " x" .. count .. " to " .. player:get_player_name()
                )
            end
            end
        end
    end
end

local function on_poll_response(player_name, res)
    if not res.completed then
        minetest.log("warning", "[agent_poller] Poll failed (not completed)")
        return
    end
    if res.code ~= 200 then
        minetest.log("warning", "[agent_poller] Poll HTTP code: " .. tostring(res.code))
        return
    end
    local ok_parse, commands = pcall(minetest.parse_json, res.data)
    if not ok_parse or not commands then
        minetest.log("warning", "[agent_poller] Poll JSON parse failed")
        return
    end
    if not commands.actions or #commands.actions == 0 then
        return
    end
    local player = nil
    for _, p in ipairs(minetest.get_connected_players()) do
        if p:get_player_name() == player_name then
            player = p
            break
        end
    end
    if not player then
        return
    end
    minetest.log("action", "[agent_poller] Executing " .. #commands.actions .. " action(s) for " .. player_name)
    execute_commands(commands.actions, player)
end

local function poll_bridge()
    local player = get_target_player()
    if not player then
        return
    end
    local player_name = player:get_player_name()
    local pos = player:get_pos()
    local inv = player:get_inventory()
    local inv_list = {}
    for i = 1, inv:get_size("main") do
        local stack = inv:get_stack("main", i)
        if not stack:is_empty() then
            inv_list[stack:get_name()] = (inv_list[stack:get_name()] or 0) + stack:get_count()
        end
    end
    local state = {
        type = "state",
        position = {x = pos.x, y = pos.y, z = pos.z},
        hp = player:get_hp(),
        max_hp = 20,
        breath = player:get_breath(),
        inventory = inv_list,
        wielded = player:get_wielded_item():get_name(),
        yaw = player:get_look_horizontal(),
        pitch = player:get_look_vertical(),
        on_ground = true,
    }
    http_api.fetch({
        url = BRIDGE_URL .. "/api/poll",
        method = "POST",
        data = minetest.write_json(state),
        extra_headers = {"Content-Type: application/json"},
        timeout = 5,
    }, function(res)
        on_poll_response(player_name, res)
    end)
end

minetest.register_globalstep(function(dtime)
    local now = minetest.get_gametime()
    if now - last_poll >= POLL_INTERVAL then
        last_poll = now
        local ok, err = pcall(poll_bridge)
        if not ok then
            minetest.log("error", "[agent_poller] poll error: " .. tostring(err))
        end
    end
end)

minetest.after(1, function()
    http_api.fetch({
        url = BRIDGE_URL .. "/health",
        timeout = 5,
    }, function(res)
        if res.completed and res.code == 200 then
            minetest.log("action", "[agent_poller] Bridge reachable, polling " .. BRIDGE_URL)
        else
            minetest.log("error", "[agent_poller] Bridge NOT reachable at " .. BRIDGE_URL)
        end
    end)
end)

minetest.log("action", "[agent_poller] Loaded, target=" .. TARGET_PLAYER_NAME .. " (fallback: first player)")
