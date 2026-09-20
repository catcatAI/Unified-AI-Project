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
        minetest.log(
            "action",
            "[agent_poller] craft failed (no recipe): "
                .. tostring(action.recipe_id or action.recipe or "auto")
        )
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

local last_dead_notice = 0

-- Active coordinate walk, per player: {path = {...}, idx = N, dest = pos, stuck = N}.
-- The library converts intents to coordinates; the poller walks the
-- engine-computed path. No blind stepping, no fighting the client.
local active_goto = {}
local goto_report = nil -- sticky status, attached to every poll state
local pending_scan = nil -- one-shot node survey, attached to next poll state
local scan_seq = 0
local pending_vision = nil -- one-shot raycast view, attached to next poll state
local vision_seq = 0

-- Face an exact world coordinate (execution-time precise; state yaw is stale).
local function face_toward(player, target)
    local eye = player:get_pos()
    eye.y = eye.y + 1.6
    if vector.distance(eye, target) < 0.1 then
        return
    end
    local rot = vector.dir_to_rotation(vector.direction(eye, target))
    player:set_look_horizontal(rot.y)
    player:set_look_vertical(rot.x)
end

-- First placeable node stack into the wield slot (slot swap; this Luanti
-- build has no set_wield_index). Returns the wielded stack or nil.
local function wield_placeable(player)
    local stack = player:get_wielded_item()
    if not stack:is_empty() and minetest.registered_nodes[stack:get_name()] then
        return stack
    end
    local inv = player:get_inventory()
    for i = 1, inv:get_size("main") do
        local s = inv:get_stack("main", i)
        if not s:is_empty() and minetest.registered_nodes[s:get_name()] then
            local wi = player:get_wield_index()
            inv:set_stack("main", wi, s)
            inv:set_stack("main", i, stack)
            return player:get_wielded_item()
        end
    end
    return nil
end

-- BODY REFLEXES: interoceptive only. Every loop below triggers on BODY
-- state (breath, burns, falling) — never on world prediction (no depth
-- checks, no sight rays, no terrain reading). Predicting the world is the
-- brain's job (coordinates + paths); the spine only answers damage that
-- is happening right now. Same principle covers hypoxia, burns, falls.
local body_track = {} -- pname -> {y = float, hp = int}
local step_hold = {} -- pname -> true while airborne (withhold steps)
local last_notice = {}

local function notice(pname, key, msg)
    local now = minetest.get_gametime()
    last_notice[pname] = last_notice[pname] or {}
    if now - (last_notice[pname][key] or -99) >= 10 then
        last_notice[pname][key] = now
        minetest.log("action", "[agent_poller] " .. msg .. " for " .. pname)
    end
end

local function rise(player, pname, why)
    local dest = vector.add(player:get_pos(), {x = 0, y = 1.5, z = 0})
    local hdef = minetest.registered_nodes[minetest.get_node(dest).name] or {}
    if not hdef.walkable then
        player:set_pos(dest)
        notice(pname, why, why)
    end
end

-- Runs every poll for the living target. Senses body, actuates at most a
-- 1.5m rise or a step-hold flag. Never reads terrain ahead.
local function sense_body(player, pname)
    local pos = player:get_pos()
    local hp = player:get_hp()
    local breath = player:get_breath()
    local prev = body_track[pname] or {y = pos.y, hp = hp}

    -- Hypoxia: oxygen deficit -> surface NOW, whatever surrounds her.
    -- (Diving in with full lungs is allowed; suffocating is not.)
    if breath < 10 then
        rise(player, pname, "gasping (breath " .. breath .. "/10)")
    end

    -- Burns: standing IN heat -> get out upward (lava pools surface).
    -- Contact is current bodily insult, not foresight.
    local feetname = minetest.get_node(pos).name
    if feetname:find("lava") or feetname:find("fire") then
        rise(player, pname, "burning on " .. feetname)
    end

    -- Falls: dropping faster than any stairs (>1.5m/poll) -> withhold
    -- steps until stable. Walking off one edge costs one harmless drop;
    -- the death spiral was step after step into the void.
    step_hold[pname] = (pos.y - prev.y) < -1.5

    body_track[pname] = {y = pos.y, hp = hp}
end

-- One collision-aware step toward dest (max ~1.5m). Tries ground level,
-- step-up, and (allow_climb) a jump-height scramble. Returns true if moved.
-- (No drowning/depth logic here: water safety is hypoxia-driven above.)
local function try_step(player, dest, allow_climb)
    local pos = player:get_pos()
    local flat = vector.new(dest.x - pos.x, 0, dest.z - pos.z)
    if vector.length(flat) < 0.05 then
        return true
    end
    flat = vector.normalize(flat)
    local dys = allow_climb and {0, 1, 2} or {0, 1}
    for _, dy in ipairs(dys) do
        local c = vector.round(
            vector.add(vector.add(pos, vector.multiply(flat, 1.5)), {x = 0, y = dy, z = 0})
        )
        local fdef = minetest.registered_nodes[minetest.get_node(c).name] or {}
        local head = vector.add(c, {x = 0, y = 1, z = 0})
        local hdef = minetest.registered_nodes[minetest.get_node(head).name] or {}
        if not fdef.walkable and not hdef.walkable then
            player:set_pos(c)
            minetest.log(
                "action",
                "[agent_poller] moved to "
                    .. minetest.pos_to_string(c, 1)
                    .. " for "
                    .. player:get_player_name()
            )
            return true
        end
    end
    return false
end

-- Start (or replace) a coordinate walk: engine path, advanced every poll.
-- max_drop 3 keeps cliff routes out of plans (fall prevention belongs to
-- coordinates, not to reflexes: the spine cannot un-fall you).
local function start_goto(player, pname, dest)
    dest = vector.round(dest)
    local pos = player:get_pos()
    if vector.distance(pos, dest) < 1.5 then
        active_goto[pname] = nil
        goto_report = {status = "arrived", dest = dest}
        return
    end
    local path = minetest.find_path(pos, dest, 16, 1, 3)
    if path and #path > 0 then
        active_goto[pname] = {path = path, idx = 1, dest = dest, stuck = 0}
        goto_report = {status = "walking", dest = dest}
        minetest.log(
            "action",
            "[agent_poller] goto "
                .. minetest.pos_to_string(dest, 1)
                .. " (" .. #path .. " wp) for " .. pname
        )
    else
        active_goto[pname] = nil
        goto_report = {status = "failed", reason = "no_path", dest = dest}
        minetest.log("action", "[agent_poller] goto failed (no path) for " .. pname)
        -- Best effort: one direct step anyway (dune buried the target).
        -- try_step turns on total blockage, so motion never just dies.
        try_step(player, dest, false)
    end
end

-- Advance the active goto one waypoint per poll. Runs inside poll_bridge
-- so walking continues smoothly even when the action queue holds
-- something else (10Hz agent vs 0.5Hz poller).
local function advance_goto(player, pname)
    local g = active_goto[pname]
    if not g then
        return
    end
    if player:get_hp() <= 0 then
        active_goto[pname] = nil
        goto_report = {status = "aborted", reason = "dead"}
        return
    end
    if step_hold[pname] then
        -- Airborne: withhold steps until stable (sense_body sets this).
        goto_report = {status = "walking", dest = g.dest}
        return
    end
    local pos = player:get_pos()
    local wp = g.path[g.idx]
    if not wp then
        active_goto[pname] = nil
        goto_report = {status = "arrived", dest = g.dest}
        minetest.log("action", "[agent_poller] arrived for " .. pname)
        return
    end
    if vector.distance(pos, wp) < 0.8 then
        g.idx = g.idx + 1
        goto_report = {status = "walking", dest = g.dest}
        return
    end
    if try_step(player, wp, false) then
        g.stuck = 0
        goto_report = {status = "walking", dest = g.dest}
    else
        g.stuck = (g.stuck or 0) + 1
        local yaw = player:get_look_horizontal()
        player:set_look_horizontal(yaw + math.pi / 4)
        if g.stuck > 8 then
            active_goto[pname] = nil
            goto_report = {status = "failed", reason = "blocked", dest = g.dest}
            minetest.log("action", "[agent_poller] goto failed (blocked) for " .. pname)
        else
            goto_report = {status = "walking", dest = g.dest}
        end
    end
end

local function execute_commands(actions, player)
    if not player or not actions then
        return
    end
    for _, action in ipairs(actions) do
        -- Dead players stay dead: skip everything physical so the loop
        -- doesn't march a corpse around (observed: hp 0 still stepping).
        -- Chat still goes through. Respawn is a human click.
        if action.type ~= "chat" and player:get_hp() <= 0 then
            local now = minetest.get_gametime()
            if now - last_dead_notice >= 10 then
                last_dead_notice = now
                minetest.log(
                    "action",
                    "[agent_poller] skipping "
                        .. tostring(action.type)
                        .. " ("
                        .. player:get_player_name()
                        .. " is dead, awaiting respawn)"
                )
            end
        elseif action.type == "move" then
            -- NOTE: no set_velocity anywhere: movement is client-authoritative
            -- and the standing-still client always wins, so velocity commands
            -- are dead weight. The single control path is coordinate stepping.
            local yaw = player:get_look_horizontal()
            local dir = vector.new(action.forward or 0, 0, action.strafe or 0)
            dir = vector.rotate(dir, vector.new(0, yaw, 0))
            local pname = player:get_player_name()
            if step_hold[pname] then
                -- Airborne: withhold steps until stable.
            else
                local flat = vector.new(dir.x, 0, dir.z)
                if vector.length(flat) > 0.05 then
                    local pos = player:get_pos()
                    local dest = vector.add(
                        pos,
                        vector.multiply(vector.normalize(flat), 1.5)
                    )
                    if not try_step(player, dest, action.jump) then
                        -- Bump-and-turn keeps a blind move from hugging walls.
                        player:set_look_horizontal(yaw + math.pi / 4)
                        minetest.log(
                            "action",
                            "[agent_poller] move blocked, turning for " .. pname
                        )
                    end
                end
            end
        elseif action.type == "goto" then
            -- Coordinate walk: engine path, advanced every poll by
            -- advance_goto (smooth even when the queue holds other actions).
            local d = action.pos
            if d and d.x and d.y and d.z then
                start_goto(player, player:get_player_name(), vector.new(d.x, d.y, d.z))
            end
        elseif action.type == "step_ahead" then
            -- "Walk N meters along current facing" as coordinates. Facing
            -- math stays in Lua (exact); the library only says how far.
            local yaw = player:get_look_horizontal()
            local dir = vector.rotate(vector.new(1, 0, 0), vector.new(0, yaw, 0))
            if action.backward then
                dir = vector.multiply(dir, -1)
            end
            local pos = player:get_pos()
            start_goto(
                player,
                player:get_player_name(),
                vector.add(pos, vector.multiply(dir, tonumber(action.dist) or 4.5))
            )
        elseif action.type == "look_at" then
            local t = action.pos
            if t and t.x and t.y and t.z then
                face_toward(player, vector.new(t.x, t.y, t.z))
            end
        elseif action.type == "dig_at" then
            local t = action.pos
            if t and t.x and t.y and t.z then
                local target = vector.round(vector.new(t.x, t.y, t.z))
                face_toward(player, target)
                local eye = player:get_pos()
                eye.y = eye.y + 1.6
                local node = minetest.get_node(target)
                if vector.distance(eye, target) <= 6.5
                    and node.name ~= "air"
                    and node.name ~= "ignore" then
                    minetest.node_dig(target, node, player)
                    minetest.log(
                        "action",
                        "[agent_poller] dug " .. node.name .. " at "
                            .. minetest.pos_to_string(target, 1)
                            .. " for " .. player:get_player_name()
                    )
                else
                    minetest.log(
                        "action",
                        "[agent_poller] dig_at failed (" .. node.name .. ") for "
                            .. player:get_player_name()
                    )
                end
            end
        elseif action.type == "place_at" then
            local t = action.pos
            if t and t.x and t.y and t.z then
                local target = vector.round(vector.new(t.x, t.y, t.z))
                face_toward(player, target)
                local below = vector.add(target, {x = 0, y = -1, z = 0})
                if minetest.get_node(target).name == "air"
                    and minetest.get_node(below).name ~= "air" then
                    local stack = wield_placeable(player)
                    if stack then
                        local placed_name = stack:get_name()
                        local leftover = minetest.item_place(
                            stack, player, {type = "node", under = below, above = target}
                        )
                        if leftover then
                            player:set_wielded_item(leftover)
                        end
                        minetest.log(
                            "action",
                            "[agent_poller] placed " .. placed_name .. " at "
                                .. minetest.pos_to_string(target, 1)
                                .. " for " .. player:get_player_name()
                        )
                    else
                        minetest.log(
                            "action",
                            "[agent_poller] place_at failed (nothing placeable) for "
                                .. player:get_player_name()
                        )
                    end
                else
                    minetest.log(
                        "action",
                        "[agent_poller] place_at failed (no free cell) for "
                            .. player:get_player_name()
                    )
                end
            end
        elseif action.type == "scan" then
            -- Node survey for intent grounding ("that tree" -> coordinates).
            -- Result rides the next poll state; the library picks from it.
            local names = action.nodes or (action.node and {action.node} or {})
            if type(names) == "string" then
                names = {names}
            end
            if #names > 0 then
                local pos = vector.round(player:get_pos())
                local r = math.min(tonumber(action.radius) or 16, 24)
                local found = minetest.find_nodes_in_area(
                    vector.subtract(pos, r), vector.add(pos, r), names
                ) or {}
                local scored = {}
                for _, p in ipairs(found) do
                    scored[#scored + 1] = {pos = p, d = vector.distance(pos, p)}
                end
                table.sort(scored, function(a, b) return a.d < b.d end)
                local items = {}
                for i = 1, math.min(#scored, 12) do
                    local p = scored[i].pos
                    items[#items + 1] = {
                        node = minetest.get_node(p).name,
                        x = p.x, y = p.y, z = p.z,
                    }
                end
                scan_seq = scan_seq + 1
                pending_scan = {seq = scan_seq, center = {x = pos.x, y = pos.y, z = pos.z}, nodes = items}
                minetest.log(
                    "action",
                    "[agent_poller] scanned " .. #items .. " nodes for "
                        .. player:get_player_name()
                )
            end
        elseif action.type == "vision" then
            -- Raycast eyes: 5 yaw x 3 pitch rays across the view frustum.
            -- Base direction comes from the engine (no yaw-convention math);
            -- small Euler offsets only spread the grid, so approximate is fine.
            -- Occluded like real sight (unlike scan); water is visible.
            local eye = player:get_pos()
            eye.y = eye.y + 1.6
            local base = player:get_look_dir()
            local range = math.min(tonumber(action.range) or 24, 32)
            local rays = {}
            for _, yo in ipairs({0, 0.4, -0.4, 0.8, -0.8}) do
                for _, po in ipairs({0, 0.35, -0.35}) do
                    local dir = vector.rotate(base, {x = po, y = yo, z = 0})
                    local rc = minetest.raycast(
                        eye, vector.add(eye, vector.multiply(dir, range)), false, false
                    )
                    local hit = {node = "air", dist = range, yaw_off = yo, pitch_off = po}
                    for pointed in rc do
                        if pointed.type == "node" then
                            local p = pointed.under
                            hit = {
                                node = minetest.get_node(p).name,
                                x = p.x, y = p.y, z = p.z,
                                dist = math.floor(vector.distance(eye, p) * 10) / 10,
                                yaw_off = yo, pitch_off = po,
                            }
                        end
                        break
                    end
                    rays[#rays + 1] = hit
                end
            end
            vision_seq = vision_seq + 1
            pending_vision = {seq = vision_seq, rays = rays}
            minetest.log(
                "action",
                "[agent_poller] vision (" .. #rays .. " rays) for "
                    .. player:get_player_name()
            )
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
                            -- No set_wield_index in this Luanti build: swap
                            -- the stack into the current wield slot instead.
                            local wi = player:get_wield_index()
                            local wielded = inv:get_stack("main", wi)
                            inv:set_stack("main", wi, s)
                            inv:set_stack("main", i, wielded)
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
                    -- Capture the name first: item_place may consume `stack`.
                    local placed_name = stack:get_name()
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
                            .. placed_name
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
    -- Body sense first (hypoxia/burn/fall flags), then walking: reflexes
    -- gate motion, never the other way around.
    if player:get_hp() > 0 then
        do
            local ok, err = pcall(sense_body, player, player_name)
            if not ok then
                minetest.log("error", "[agent_poller] sense_body failed: " .. tostring(err))
            end
        end
    end
    -- Coordinate walk advances every poll, independent of queued actions.
    do
        local ok, err = pcall(advance_goto, player, player_name)
        if not ok then
            minetest.log("error", "[agent_poller] goto advance failed: " .. tostring(err))
        end
    end
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
        goto_ = goto_report,
        scan = pending_scan,
        vision = pending_vision,
    }
    pending_scan = nil -- one-shot deliveries; goto_ stays sticky
    pending_vision = nil
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

-- Forward player chat to the bridge so the agent hears it. Returning
-- false lets the message show normally. The agent's own "[Angela] ..."
-- lines go through chat_send_all and never re-enter here: no loop.
minetest.register_on_chat_message(function(name, message)
    local ok, err = pcall(http_api.fetch, {
        url = BRIDGE_URL .. "/api/chat",
        method = "POST",
        data = minetest.write_json({type = "chat", player = name, message = message}),
        extra_headers = {"Content-Type: application/json"},
        timeout = 5,
    }, function(_) end)
    if not ok then
        minetest.log("warning", "[agent_poller] chat forward failed: " .. tostring(err))
    end
    return false
end)

minetest.log("action", "[agent_poller] Loaded, target=" .. TARGET_PLAYER_NAME .. " (fallback: first player)")
