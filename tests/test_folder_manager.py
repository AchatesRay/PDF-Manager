"""文件夹管理器测试"""

import pytest
import tempfile
from pathlib import Path

from src.models.database import Database
from src.models.schemas import Folder, PDF
from src.core.folder_manager import FolderManager


@pytest.fixture
def temp_db_path():
    """创建临时数据库路径"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test.db"


@pytest.fixture
def db(temp_db_path):
    """创建数据库实例"""
    return Database(temp_db_path)


@pytest.fixture
def folder_manager(db):
    """创建文件夹管理器实例"""
    return FolderManager(db)


class TestFolderManagerInit:
    """文件夹管理器初始化测试"""

    def test_init(self, db):
        """测试初始化"""
        manager = FolderManager(db)
        assert manager is not None


class TestCreateFolder:
    """创建文件夹测试"""

    def test_create_root_folder(self, folder_manager):
        """测试创建根文件夹"""
        folder = folder_manager.create_folder("根文件夹")
        assert folder.id is not None
        assert folder.name == "根文件夹"
        assert folder.parent_id is None

    def test_create_nested_folder(self, folder_manager):
        """测试创建嵌套文件夹"""
        parent = folder_manager.create_folder("父文件夹")
        child = folder_manager.create_folder("子文件夹", parent_id=parent.id)

        assert child.id is not None
        assert child.name == "子文件夹"
        assert child.parent_id == parent.id

    def test_create_folder_with_nonexistent_parent(self, folder_manager):
        """测试创建文件夹时父文件夹不存在"""
        with pytest.raises(ValueError, match="Parent folder with id 999 does not exist"):
            folder_manager.create_folder("测试文件夹", parent_id=999)

    def test_create_multiple_folders(self, folder_manager):
        """测试创建多个文件夹"""
        folder1 = folder_manager.create_folder("文件夹A")
        folder2 = folder_manager.create_folder("文件夹B")
        folder3 = folder_manager.create_folder("文件夹C")

        assert folder1.id != folder2.id
        assert folder2.id != folder3.id
        assert folder1.id != folder3.id


class TestGetFolder:
    """获取文件夹测试"""

    def test_get_folder(self, folder_manager):
        """测试获取文件夹"""
        created = folder_manager.create_folder("测试文件夹")
        folder = folder_manager.get_folder(created.id)

        assert folder is not None
        assert folder.id == created.id
        assert folder.name == "测试文件夹"

    def test_get_folder_not_found(self, folder_manager):
        """测试获取不存在的文件夹"""
        folder = folder_manager.get_folder(999)
        assert folder is None


class TestGetRootFolders:
    """获取根文件夹测试"""

    def test_get_root_folders_empty(self, folder_manager):
        """测试空数据库获取根文件夹"""
        folders = folder_manager.get_root_folders()
        assert folders == []

    def test_get_root_folders(self, folder_manager):
        """测试获取根文件夹列表"""
        root1 = folder_manager.create_folder("根文件夹1")
        root2 = folder_manager.create_folder("根文件夹2")

        # 创建一个子文件夹
        folder_manager.create_folder("子文件夹", parent_id=root1.id)

        roots = folder_manager.get_root_folders()
        assert len(roots) == 2
        root_ids = [f.id for f in roots]
        assert root1.id in root_ids
        assert root2.id in root_ids


class TestGetChildFolders:
    """获取子文件夹测试"""

    def test_get_child_folders_empty(self, folder_manager):
        """测试获取空文件夹的子文件夹"""
        parent = folder_manager.create_folder("父文件夹")
        children = folder_manager.get_child_folders(parent.id)
        assert children == []

    def test_get_child_folders(self, folder_manager):
        """测试获取子文件夹列表"""
        parent = folder_manager.create_folder("父文件夹")
        child1 = folder_manager.create_folder("子文件夹1", parent_id=parent.id)
        child2 = folder_manager.create_folder("子文件夹2", parent_id=parent.id)

        # 创建其他根文件夹
        folder_manager.create_folder("其他文件夹")

        children = folder_manager.get_child_folders(parent.id)
        assert len(children) == 2
        child_ids = [f.id for f in children]
        assert child1.id in child_ids
        assert child2.id in child_ids


class TestGetAllFolders:
    """获取所有文件夹测试"""

    def test_get_all_folders_empty(self, folder_manager):
        """测试空数据库获取所有文件夹"""
        folders = folder_manager.get_all_folders()
        assert folders == []

    def test_get_all_folders(self, folder_manager):
        """测试获取所有文件夹"""
        root = folder_manager.create_folder("根文件夹")
        child = folder_manager.create_folder("子文件夹", parent_id=root.id)

        folders = folder_manager.get_all_folders()
        assert len(folders) == 2
        folder_ids = [f.id for f in folders]
        assert root.id in folder_ids
        assert child.id in folder_ids


class TestRenameFolder:
    """重命名文件夹测试"""

    def test_rename_folder(self, folder_manager):
        """测试重命名文件夹"""
        folder = folder_manager.create_folder("原名称")
        result = folder_manager.rename_folder(folder.id, "新名称")

        assert result is True
        renamed = folder_manager.get_folder(folder.id)
        assert renamed.name == "新名称"

    def test_rename_folder_not_found(self, folder_manager):
        """测试重命名不存在的文件夹"""
        result = folder_manager.rename_folder(999, "新名称")
        assert result is False


class TestMoveFolder:
    """移动文件夹测试"""

    def test_move_folder_to_root(self, folder_manager):
        """测试移动文件夹到根目录"""
        parent = folder_manager.create_folder("父文件夹")
        child = folder_manager.create_folder("子文件夹", parent_id=parent.id)

        # 移动到根目录
        result = folder_manager.move_folder(child.id, None)
        assert result is True

        moved = folder_manager.get_folder(child.id)
        assert moved.parent_id is None

    def test_move_folder_to_another_parent(self, folder_manager):
        """测试移动文件夹到另一个父文件夹"""
        parent1 = folder_manager.create_folder("父文件夹1")
        parent2 = folder_manager.create_folder("父文件夹2")
        child = folder_manager.create_folder("子文件夹", parent_id=parent1.id)

        # 移动到另一个父文件夹
        result = folder_manager.move_folder(child.id, parent2.id)
        assert result is True

        moved = folder_manager.get_folder(child.id)
        assert moved.parent_id == parent2.id

    def test_move_folder_to_same_parent(self, folder_manager):
        """测试移动文件夹到同一父文件夹"""
        parent = folder_manager.create_folder("父文件夹")
        child = folder_manager.create_folder("子文件夹", parent_id=parent.id)

        # 移动到同一位置
        result = folder_manager.move_folder(child.id, parent.id)
        assert result is True

        moved = folder_manager.get_folder(child.id)
        assert moved.parent_id == parent.id

    def test_move_folder_not_found(self, folder_manager):
        """测试移动不存在的文件夹"""
        result = folder_manager.move_folder(999, None)
        assert result is False

    def test_move_folder_to_nonexistent_parent(self, folder_manager):
        """测试移动文件夹到不存在的父文件夹"""
        folder = folder_manager.create_folder("测试文件夹")

        with pytest.raises(ValueError, match="Target folder with id 999 does not exist"):
            folder_manager.move_folder(folder.id, 999)

    def test_move_folder_to_self_cycle(self, folder_manager):
        """测试移动文件夹到自己（循环引用）"""
        folder = folder_manager.create_folder("测试文件夹")

        with pytest.raises(ValueError, match="would create a cycle"):
            folder_manager.move_folder(folder.id, folder.id)

    def test_move_folder_to_descendant_cycle(self, folder_manager):
        """测试移动文件夹到自己的后代（循环引用）"""
        grandparent = folder_manager.create_folder("祖父文件夹")
        parent = folder_manager.create_folder("父文件夹", parent_id=grandparent.id)
        child = folder_manager.create_folder("子文件夹", parent_id=parent.id)

        # 尝试将祖父文件夹移动到子文件夹下
        with pytest.raises(ValueError, match="would create a cycle"):
            folder_manager.move_folder(grandparent.id, child.id)

    def test_move_folder_deep_hierarchy(self, folder_manager):
        """测试深层嵌套的循环引用检测"""
        # 创建层级结构: A -> B -> C -> D
        a = folder_manager.create_folder("A")
        b = folder_manager.create_folder("B", parent_id=a.id)
        c = folder_manager.create_folder("C", parent_id=b.id)
        d = folder_manager.create_folder("D", parent_id=c.id)

        # 尝试将A移动到D下（应该失败）
        with pytest.raises(ValueError, match="would create a cycle"):
            folder_manager.move_folder(a.id, d.id)

        # 将D移动到A下（应该成功，因为D是叶子节点，不会产生循环）
        result = folder_manager.move_folder(d.id, a.id)
        assert result is True
        moved_d = folder_manager.get_folder(d.id)
        assert moved_d.parent_id == a.id


class TestDeleteFolder:
    """删除文件夹测试"""

    def test_delete_empty_folder(self, folder_manager):
        """测试删除空文件夹"""
        folder = folder_manager.create_folder("待删除文件夹")
        result = folder_manager.delete_folder(folder.id)

        assert result is True
        assert folder_manager.get_folder(folder.id) is None

    def test_delete_folder_not_found(self, folder_manager):
        """测试删除不存在的文件夹"""
        result = folder_manager.delete_folder(999)
        assert result is False

    def test_delete_folder_with_subfolders_no_force(self, folder_manager):
        """测试删除有子文件夹的文件夹（不强制删除）"""
        parent = folder_manager.create_folder("父文件夹")
        folder_manager.create_folder("子文件夹", parent_id=parent.id)

        with pytest.raises(ValueError, match="folder has subfolders"):
            folder_manager.delete_folder(parent.id)

    def test_delete_folder_with_subfolders_force(self, folder_manager):
        """测试删除有子文件夹的文件夹（强制删除）"""
        parent = folder_manager.create_folder("父文件夹")
        child = folder_manager.create_folder("子文件夹", parent_id=parent.id)

        result = folder_manager.delete_folder(parent.id, delete_contents=True)
        assert result is True
        assert folder_manager.get_folder(parent.id) is None
        assert folder_manager.get_folder(child.id) is None

    def test_delete_folder_with_pdfs_no_force(self, folder_manager, db):
        """测试删除有PDF的文件夹（不强制删除）"""
        folder = folder_manager.create_folder("文件夹")
        pdf = PDF(filename="test.pdf", file_path="/test.pdf", folder_id=folder.id)
        db.create_pdf(pdf)

        with pytest.raises(ValueError, match="folder contains PDF files"):
            folder_manager.delete_folder(folder.id)

    def test_delete_folder_with_pdfs_force(self, folder_manager, db):
        """测试删除有PDF的文件夹（强制删除）"""
        folder = folder_manager.create_folder("文件夹")
        pdf = PDF(filename="test.pdf", file_path="/test.pdf", folder_id=folder.id)
        pdf_id = db.create_pdf(pdf)

        result = folder_manager.delete_folder(folder.id, delete_contents=True)
        assert result is True
        assert folder_manager.get_folder(folder.id) is None
        assert db.get_pdf(pdf_id) is None

    def test_delete_folder_recursive(self, folder_manager, db):
        """测试递归删除文件夹及其所有内容"""
        # 创建层级结构
        root = folder_manager.create_folder("根文件夹")
        child1 = folder_manager.create_folder("子文件夹1", parent_id=root.id)
        child2 = folder_manager.create_folder("子文件夹2", parent_id=root.id)
        grandchild = folder_manager.create_folder("孙文件夹", parent_id=child1.id)

        # 添加PDF文件
        pdf1 = PDF(filename="pdf1.pdf", file_path="/pdf1.pdf", folder_id=root.id)
        pdf2 = PDF(filename="pdf2.pdf", file_path="/pdf2.pdf", folder_id=child1.id)
        pdf1_id = db.create_pdf(pdf1)
        pdf2_id = db.create_pdf(pdf2)

        # 删除根文件夹
        result = folder_manager.delete_folder(root.id, delete_contents=True)

        assert result is True
        assert folder_manager.get_folder(root.id) is None
        assert folder_manager.get_folder(child1.id) is None
        assert folder_manager.get_folder(child2.id) is None
        assert folder_manager.get_folder(grandchild.id) is None
        assert db.get_pdf(pdf1_id) is None
        assert db.get_pdf(pdf2_id) is None


class TestGetFolderPath:
    """获取文件夹路径测试"""

    def test_get_folder_path_not_found(self, folder_manager):
        """测试获取不存在文件夹的路径"""
        path = folder_manager.get_folder_path(999)
        assert path == []

    def test_get_folder_path_root(self, folder_manager):
        """测试获取根文件夹的路径"""
        root = folder_manager.create_folder("根文件夹")
        path = folder_manager.get_folder_path(root.id)

        assert len(path) == 1
        assert path[0].id == root.id
        assert path[0].name == "根文件夹"

    def test_get_folder_path_nested(self, folder_manager):
        """测试获取嵌套文件夹的路径"""
        grandparent = folder_manager.create_folder("祖父文件夹")
        parent = folder_manager.create_folder("父文件夹", parent_id=grandparent.id)
        child = folder_manager.create_folder("子文件夹", parent_id=parent.id)

        path = folder_manager.get_folder_path(child.id)

        assert len(path) == 3
        assert path[0].id == grandparent.id
        assert path[0].name == "祖父文件夹"
        assert path[1].id == parent.id
        assert path[1].name == "父文件夹"
        assert path[2].id == child.id
        assert path[2].name == "子文件夹"

    def test_get_folder_path_deep_hierarchy(self, folder_manager):
        """测试获取深层嵌套文件夹的路径"""
        # 创建5层嵌套
        folders = []
        current_parent = None
        for i in range(5):
            folder = folder_manager.create_folder(f"文件夹{i}", parent_id=current_parent)
            folders.append(folder)
            current_parent = folder.id

        # 获取最深层文件夹的路径
        path = folder_manager.get_folder_path(folders[-1].id)

        assert len(path) == 5
        for i, folder in enumerate(folders):
            assert path[i].id == folder.id
            assert path[i].name == f"文件夹{i}"


class TestFolderManagerIntegration:
    """文件夹管理器集成测试"""

    def test_create_update_delete_workflow(self, folder_manager):
        """测试创建、更新、删除工作流"""
        # 创建
        folder = folder_manager.create_folder("初始名称")
        assert folder.name == "初始名称"

        # 更新
        result = folder_manager.rename_folder(folder.id, "更新后名称")
        assert result is True
        updated = folder_manager.get_folder(folder.id)
        assert updated.name == "更新后名称"

        # 删除
        result = folder_manager.delete_folder(folder.id)
        assert result is True
        assert folder_manager.get_folder(folder.id) is None

    def test_complex_folder_structure(self, folder_manager):
        """测试复杂的文件夹结构操作"""
        # 创建一个复杂的层级结构
        #     root1
        #     /   \
        #   child1 child2
        #    |
        #  grandchild
        #     root2

        root1 = folder_manager.create_folder("root1")
        root2 = folder_manager.create_folder("root2")
        child1 = folder_manager.create_folder("child1", parent_id=root1.id)
        child2 = folder_manager.create_folder("child2", parent_id=root1.id)
        grandchild = folder_manager.create_folder("grandchild", parent_id=child1.id)

        # 验证结构
        roots = folder_manager.get_root_folders()
        assert len(roots) == 2

        root1_children = folder_manager.get_child_folders(root1.id)
        assert len(root1_children) == 2

        # 验证路径
        path = folder_manager.get_folder_path(grandchild.id)
        assert len(path) == 3
        assert path[0].id == root1.id
        assert path[1].id == child1.id
        assert path[2].id == grandchild.id

        # 移动 grandchild 到 root2
        folder_manager.move_folder(grandchild.id, root2.id)
        moved = folder_manager.get_folder(grandchild.id)
        assert moved.parent_id == root2.id

        # 验证 root2 的子文件夹
        root2_children = folder_manager.get_child_folders(root2.id)
        assert len(root2_children) == 1
        assert root2_children[0].id == grandchild.id

    def test_all_folders_after_operations(self, folder_manager):
        """测试在多个操作后获取所有文件夹"""
        # 创建多个文件夹
        folder1 = folder_manager.create_folder("文件夹1")
        folder2 = folder_manager.create_folder("文件夹2", parent_id=folder1.id)
        folder3 = folder_manager.create_folder("文件夹3", parent_id=folder1.id)
        folder4 = folder_manager.create_folder("文件夹4")

        # 验证所有文件夹
        all_folders = folder_manager.get_all_folders()
        assert len(all_folders) == 4

        # 删除一个
        folder_manager.delete_folder(folder4.id)

        # 再次验证
        all_folders = folder_manager.get_all_folders()
        assert len(all_folders) == 3