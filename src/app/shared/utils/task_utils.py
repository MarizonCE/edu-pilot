"""
与任务相关的模块
"""

# key: task_id, value: 节点名列表
_tasks_running_list: dict[str, list[str]] = {}
_tasks_done_list: dict[str, list[str]] = {}

# key: task_id, value: 任务结果
_tasks_result_list: dict[str, list[str]] = {}


def _ensure_task(task_id: str) -> None:
    """确保 task_id 对应的数据结构已经初始化"""
    if task_id not in _tasks_running_list:
        _tasks_running_list[task_id] = []
    if task_id not in _tasks_done_list:
        _tasks_done_list[task_id] = []
    if task_id not in _tasks_result_list:
        _tasks_result_list[task_id] = []


def add_running_task(task_id: str, node_name: str, is_stream: bool = False) -> None:
    """添加“正在运行”的节点任务"""
    _ensure_task(task_id)
    running = _tasks_running_list[task_id]

    # 避免重复追加
    if node_name not in running:
        running.append(node_name)

    if is_stream:
        task_push_queue(task_id)


def add_done_task(task_id: str, node_name: str, is_stream: bool = False) -> None:
    """添加“已完成”的节点任务"""
    # 从 running 中移除已经完成的节点，不用 remove 是因为里面可能有多个同名的节点，要移除所有这些节点
    _ensure_task(task_id)
    running = _tasks_running_list[task_id]
    _tasks_running_list[task_id] = [n for n in running if n != node_name]

    done = _tasks_done_list[task_id]
    if node_name not in done:
        done.append(node_name)

    if is_stream:
        task_push_queue(task_id)


def task_push_queue(task_id: str) -> None:
    pass
