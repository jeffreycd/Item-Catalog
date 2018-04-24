from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Category, Item, Base, User

engine = create_engine('postgresql://catalog:fr3Ed0@localhost/catalog')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
User = User(name="Dummy", email="dummy@mailinator.com")
session.add(User)
session.commit()

# Create several catagories
category = Category(id=1, name="Soccer")

session.add(category)
session.commit()

category = Category(id=2, name="Baseball")

session.add(category)
session.commit()

category = Category(id=3, name="Basketball")

session.add(category)
session.commit()

category = Category(id=4, name="Hiking")

session.add(category)
session.commit()

category = Category(id=5, name="Golfing")

session.add(category)
session.commit()

category = Category(id=6, name="Pro Wrestling")

session.add(category)
session.commit()

item = Item(id=1, name="Wood Bat", description="A bat made of wood!",
            category_id=2, user_id=1)

session.add(item)
session.commit()

item = Item(id=2, name="Catchers Mit",
            description="A glove specially made for Catchers. Provides extra \
            padding for the fastest of pitches.",
            category_id=2, user_id=1)

session.add(item)
session.commit()

item = Item(id=3, name="Metal Folding Chair",
            description="A folding chair made of metal. Won't dent no matter \
            how hard you hit your opponent!",
            category_id=6, user_id=1)

session.add(item)
session.commit()

item = Item(id=4, name="Cleets",
            description="Shoes specially designed for playing Soccer \
            (Football).",
            category_id=1, user_id=1)

session.add(item)
session.commit()

print "added categories!"
