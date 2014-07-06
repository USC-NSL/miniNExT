"""
Mount support for MiniNExT.
"""


class MountProperties(object):

    "Contains the properties needed by a mount handler"

    def __init__(self, target, source=None):
        """initializes a mount properties object
           target: either a PathProperties object or a path string
           source: either a PathProperties object or a path string"""
        self.target = target
        self.source = source


class PathProperties(object):

    "Contains properties of a path along with options for actions to take"

    def __init__(
            self,
            path,
            perms=None,
            create=None,
            createRecursive=None,
            setPerms=None,
            checkPerms=None):
        "initializes a path properties object"
        self.path = path
        self.perms = perms
        self.create = create
        self.createRecursive = createRecursive
        self.setPerms = setPerms
        self.checkPerms = checkPerms


class ObjectPermissions(object):

    "Containers the permission properties of an object / path"

    def __init__(self, username=None, uid=None, groupname=None, gid=None,
                 mode=None, strictMode=None, enforceRecursive=None):
        "initializes an object permissions object"
        self.username = username
        self.uid = uid
        self.groupname = groupname
        self.gid = gid
        self.mode = mode
        self.strictMode = strictMode
        self.enforceRecursive = enforceRecursive
