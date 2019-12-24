from orm import Model,StringField,IntegerField

class User(Model):
	__table__ = 'users'

	id = IntegerField(primary_key = True)
	name = StringField()

# 注意到定义在User类中的__table__、id和name是类的属性，不是实例的属性。所以，在类级别上定义的属性用来描述User对象和表的映射关系，而实例属性必须通过__init__()方法去初始化，所以两者互不干扰：
# 类的属性和实例的属性


user = User(id = 123,name = 'Michael')

user.insert()

users = User.findAll()

class Model(dict,metaclass = ModelMetaclass):

	def __init__(self,**kw):
		super(Model,self).__init__(**kw)

	def __getattr__(self,key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError(r"'Model' object has no attribute '%s'"%key)

	def __setattr__(self,key,value):
		self[key] = value

	def getValue(self,key):
		return getattr(self,key,None)

	def getValueOrDefault(self,key):
		value = getattr(self,key,None)
		if value is None:
			field = self.__mappings__[key]
			if field.default is not None:
				value = field.default() if callable(field.default) else field.default
				logging.debug('using default value for %s: %s'%(key, str(value)))
				setattr(self,key,value)
		return value

	@asyncio.coroutine
	def save(self):
		args = list(map(self.getValueOrDefault,self.__fields__))
		args.append(self.getValueOrDefault(self.__primary_key__))
		rows = yield from execute(self.__insert__,args)
		if rows != 1:
			logging.warn('failed to insert record: affected rows: %s'% rows)


	@classmethod
	@asyncio.coroutine
	def find(cls,pk):
		' find object by primary key.'
		rs = yield from select('%s where `%s`=?'%(cls.__select__,cls.__primary_key__),[pk],1)
		if len(rs) = 0:
			return None
		return cls(**rs[0])

	

#Field和各种Field子类
class Field(object):

	def __init__(self,name,column_type,primary_key,default):
		self.name
		self.column_type = column_type
		self.primary_key = primary_key
		self.default = default
	
	def __str__(self):
		return '<%s,%s:%s>'%(self.__class__.__name__,self.column_type,self.name)

class StringField(Field):
	def __init__(self,name = None,primary_key=False,default=None,ddl='varchar(100'):
		super().__init__(name,ddl,primary_key,default)

class ModelMetaclass(type):
	def __new__(cls,name,bases,attrs):
		#排除Model类本身:
		if name = "Model":
			return type.__new__(cls,name,bases,attrs)
		#获取table名称:
		tableName = attrs.get('__table__',None) or name
		logging.info('found model: %s (table: %s)'% (name,tableName))
		#获取所有Field和主键名:
		mappings = dict()
		fields = []
		primaryKey = None
		for k,v in attrs.items():
			if isinstance(v,Field):
				logging.info('  found mapping: %s ==> %s'%(k,v))
				mappings[k] = v
				if v.primary_key:
					#找到主键:
					if primaryKey:
						raise RuntimeError('Duplicate primary key for field: %s'%k)
					primaryKey = k

				else:
					fields.append(k)
		if not primaryKey:
			raise RuntimeError('Primary key not found.')
		for k in mappings.keys():
			attrs.pop(k)
		escaped_fields = list(map(lambda f: '`%s`' % f,fields))
		#保存属性和列的映射关系
		attrs['__mappings__'] = mappings
		attrs['__table__'] = tableName
		#主键属性名
		attrs['__primary_key__'] = primaryKey
		#除主键外的属性名
		attrs['__fields__'] = fields

		#构造默认的SELECT, INSERT, UPDATE和DELETE语句:
		attrs['__select__'] = 'select `%s`,%s from `%s`'%(primaryKey,','.join(escaped_fields),tableName)
		attrs['__insert__'] = 'insert into `%s` (%s,`%s`) values (%s)' % (tableName,','.join(escaped_fields),primaryKey,create_args_string(len(escaped_fields)+1))
		attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName,','.join(map(lambda f:'`%s`=?'%(mappings.get(f).name or f ),fields)),primaryKey)
		attrs['__delete'] = 'delete from `%s` where `%s`=?' % (tableName,primaryKey)
		return type.__new__(cls,name,bases,attrs)






