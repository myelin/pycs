import pycs_settings

class updatesDb:
	"Object to hold info on updated weblogs"
	def __init__( self, set ):
		self.set = set
		self.updatesTable = self.set.db.getas(
			'weblogUpdates[updateTime:S,blogName:S,blogUrl:S]'
			).ordered( 3 )
		
	def Update( self, blogName, blogUrl ):
		"Mark a blog as updated"
		tbl = self.updatesTable
		while 1:
			idx = tbl.find( blogName=blogName, blogUrl=blogUrl )
			if idx == -1: break
			tbl.delete( idx )
		tbl.append( updateTime=self.set.GetTime(), blogName=blogName, blogUrl=blogUrl )
		self.set.Commit()
		