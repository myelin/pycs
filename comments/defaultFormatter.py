
class defaultFormatter:
	def contentType( self ):
		raise NotImplementedException()

	def header( self ):
		return ""
		
	def startTable( self ):
		return ""
	
	def endTable( self ):
		return ""

	def footer( self ):
		return ""
		