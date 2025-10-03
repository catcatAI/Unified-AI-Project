#!/usr/bin/env python3
"""
修复HSP集成测试中的消息传递问题
"""
import sys
import os

# 添加项目路径
project_root: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_path: str = os.path.join(project_root, 'apps', 'backend')
sys.path.insert(0, backend_path)
sys.path.insert(0, os.path.join(backend_path, 'src'))

def fix_hsp_connector_publish()
    """修复HSP连接器中的消息发布问题"""
    try:
    # 读取HSP连接器文件
    connector_path = os.path.join(backend_path, 'src', 'hsp', 'connector.py')
    with open(connector_path, 'r', encoding='utf-8') as f:
    content = f.read()

    # 检查是否已经修复
        if 'asyncio.iscoroutinefunction(mqtt_client.publish)' in content:

    print("✓ HSP连接器已经修复")
            return True

    # 修复_publish_fact方法
        if 'async def publish_fact' in content:
            # 确保publish_fact方法正确实现
            lines = content.split('\n')
            new_lines = []
            in_publish_fact = False
            publish_fact_fixed = False

            for line in lines:


    if 'async def publish_fact' in line:



    in_publish_fact = True
                    new_lines.append(line)
                elif in_publish_fact and 'return success' in line
                    # 在return之前添加日志
                    new_lines.append('            ')
                    new_lines.append('            if success:')
                    new_lines.append('                self.logger.info(f"Fact {fact_payload.get(\'id\')} published successfully.")')
                    new_lines.append('            else:')
                    new_lines.append('                self.logger.error(f"Failed to publish fact {fact_payload.get(\'id\')}.").replace(").replace(", "")
                    new_lines.append('                ')
                    new_lines.append('            return success')
                    in_publish_fact = False
                    publish_fact_fixed = True
                elif 'async def _raw_publish_message' in line and not publish_fact_fixed:
                    # 如果publish_fact没有被修复，添加完整的修复
                    if not in_publish_fact:

    new_lines.append('    async def publish_fact(self, fact_payload: HSPFactPayload) -> bool:')
                        new_lines.append('        """')
                        new_lines.append('        Publishes a fact to the HSP network.')
                        new_lines.append('        ')
                        new_lines.append('        Args:')
                        new_lines.append('            fact_payload: The fact to publish.')
                        new_lines.append('            ')
                        new_lines.append('        Returns:')
                        new_lines.append('            bool: True if the fact was published successfully, False otherwise.')
    new_lines.append('        """')
                        new_lines.append('        try:')
                        new_lines.append('            # Create the HSP message envelope')
                        new_lines.append('            envelope: HSPMessageEnvelope = self._create_envelope(')
                        new_lines.append('                message_type="HSP::Fact",')
                        new_lines.append('                payload=fact_payload,')
                        new_lines.append('                payload_schema_uri=get_schema_uri("HSP_Fact_v0.1.schema.json")')
                        new_lines.append('            )')
                        new_lines.append('            ')
                        new_lines.append('            # Use the standard fact topic')
                        new_lines.append('            topic = f"hsp/knowledge/facts/{self.ai_id}"')
                        new_lines.append('            ')
                        new_lines.append('            # Publish the message')
                        new_lines.append('            success = await self.publish_message(topic, envelope)')
                        new_lines.append('            ')
                        new_lines.append('            if success:')
                        new_lines.append('                self.logger.info(f"Fact {fact_payload.get(\'id\')} published successfully.")')
                        new_lines.append('            else:')
                        new_lines.append('                self.logger.error(f"Failed to publish fact {fact_payload.get(\'id\')}."))')
                        new_lines.append('                ')
                        new_lines.append('            return success')
                        new_lines.append('            ')
                        new_lines.append('        except Exception as e:')
                        new_lines.append('            self.logger.error(f"Error publishing fact: {e}", exc_info=True)')
                        new_lines.append('            return False')
                        new_lines.append('')
                    new_lines.append(line)
                else:

                    new_lines.append(line)

            # 写入修复后的内容
            with open(connector_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

            print("✓ HSP连接器修复完成")
            return True
        else:

            print("✗ 未找到publish_fact方法")
            return False

    except Exception as e:


    print(f"✗ 修复HSP连接器时出错: {e}")
    return False

def fix_message_bridge()
    """修复消息桥接器中的问题"""
    try:
    # 读取消息桥接器文件
    bridge_path = os.path.join(backend_path, 'src', 'hsp', 'bridge', 'message_bridge.py')
    with open(bridge_path, 'r', encoding='utf-8') as f:
    content = f.read()

    # 检查是否已经修复
        if 'asyncio.iscoroutinefunction' in content:

    print("✓ 消息桥接器已经修复")
            return True

    # 修复消息处理方法
        if 'async def handle_external_message' in content:

    lines = content.split('\n')
            new_lines = []

            for line in lines:
                # 确保回调函数正确处理
                if 'callback(' in line and not 'await' in line and 'callback' in line:
                    # 检查callback是否是异步函数
                    new_lines.append('                if asyncio.iscoroutinefunction(callback)')
                    new_lines.append('                    await callback(payload_dict)')
                    new_lines.append('                else:')
                    new_lines.append('                    callback(payload_dict)')
                else:

                    new_lines.append(line)

            # 写入修复后的内容
            with open(bridge_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

            print("✓ 消息桥接器修复完成")
            return True
        else:

            print("✗ 未找到handle_external_message方法")
            return False

    except Exception as e:


    print(f"✗ 修复消息桥接器时出错: {e}")
    return False

def fix_service_discovery()
    """修复服务发现模块中的能力发现问题"""
    try:
    # 读取服务发现模块文件
    sd_path = os.path.join(backend_path, 'src', 'core_ai', 'service_discovery', 'service_discovery_module.py')
    with open(sd_path, 'r', encoding='utf-8') as f:
    content = f.read()

    # 检查是否已经修复
        if 'capability_name_filter.lower()' in content:

    print("✓ 服务发现模块已经修复")
            return True

    # 修复find_capabilities方法中的名称过滤
        if 'def find_capabilities' in content:

    lines = content.split('\n')
            new_lines = []
            in_find_capabilities = False

            for line in lines:


    if 'def find_capabilities' in line:



    in_find_capabilities = True
                    new_lines.append(line)
                elif in_find_capabilities and '# Apply capability_name_filter' in line
                    # 添加更灵活的名称匹配
                    new_lines.append('                # Apply capability_name_filter with more flexible matching')
    new_lines.append('                if capability_name_filter:')
                    new_lines.append('                    payload_name = payload.get(\'name\', \'\')')
                    new_lines.append('                    # Exact match')
                    new_lines.append('                    if payload_name == capability_name_filter:')
                    new_lines.append('                        logger.debug("Found capability %s with exact name match: %s", capability_id, payload_name)')
                    new_lines.append('                    # Partial match (contains)')
                    new_lines.append('                    elif capability_name_filter.lower() in payload_name.lower()')
                    new_lines.append('                        logger.debug("Found capability %s with partial name match: %s contains %s", capability_id, payload_name, capability_name_filter)')
                    new_lines.append('                    else:')
                    new_lines.append('                        logger.debug("Skipping capability %s: Name filter mismatch (expected %s, got %s)", capability_id, capability_name_filter, payload_name)')
                    new_lines.append('                        continue')
                elif in_find_capabilities and 'payload.get(\'name\') != capability_name_filter' in line:
                    # 跳过这一行，因为我们已经替换了
                    continue
                else:

                    new_lines.append(line)
                    if in_find_capabilities and line.strip() == '':

    in_find_capabilities = False

            # 写入修复后的内容
            with open(sd_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

            print("✓ 服务发现模块修复完成")
            return True
        else:

            print("✗ 未找到find_capabilities方法")
            return False

    except Exception as e:


    print(f"✗ 修复服务发现模块时出错: {e}")
    return False

def main() -> None:
    """主函数"""
    print("开始修复HSP集成测试中的问题...")
    print("=" * 50)

    # 运行所有修复
    fixes = [
    ("HSP连接器消息发布", fix_hsp_connector_publish),
    ("消息桥接器", fix_message_bridge),
    ("服务发现模块", fix_service_discovery)
    ]

    results = []
    for fix_name, fix_func in fixes:

    try:


            result = fix_func()
            results.append((fix_name, result))
        except Exception as e:

            print(f"✗ {fix_name}修复执行失败: {e}")
            results.append((fix_name, False))

    # 输出总结
    print("\n" + "=" * 50)
    print("修复结果总结:")
    all_passed = True
    for fix_name, result in results:

    status = "✓ 成功" if result else "✗ 失败":
    print(f"  {fix_name}: {status}")
        if not result:

    all_passed = False

    if all_passed:


    print("\n🎉 所有修复都成功完成！")
    return 0
    else:

    print("\n❌ 部分修复失败，请手动检查相关模块。")
    return 1

if __name__ == "__main__":


    sys.exit(main())