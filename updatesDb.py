import time

class updatesDb:
	"Object to hold info on updated weblogs"
	def __init__( self, set ):
		self.set = set
		self.updatesTable = self.set.db.getas(
			'blogUpdates[updateTime:I,blogUrl:S,blogName:S]'
			).ordered( 2 )
		
	def Update( self, blogName, blogUrl ):
		"Mark a blog as updated"
		tbl = self.updatesTable
		while 1:
			idx = tbl.find( blogName=blogName, blogUrl=blogUrl )
			if idx == -1: break
			tbl.delete( idx )
		tbl.append( updateTime=time.time(), blogName=blogName, blogUrl=blogUrl )
		self.set.Commit()

