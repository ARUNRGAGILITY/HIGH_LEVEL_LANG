# Simple Examples for PseudoJava Features

## 1. Template Synonyms

### Using `template` (Original)

```python
template Car
    instance vars:
        * name as string
    constructor:
        * name:
    instance methods:
        * getName() returns string
            return name

main
    create car as Car with "Toyota"
    print {{car.getName()}}
```

### Using `blueprint` (Architectural)

```python
blueprint House
    instance vars:
        * rooms as int
    constructor:
        * rooms:
    instance methods:
        * getRooms() returns int
            return rooms

main
    create house as House with 5
    print House has {{house.getRooms()}} rooms
```

### Using `design` (Creative)

```python
design Logo
    instance vars:
        * color as string
    constructor:
        * color:
    instance methods:
        * getColor() returns string
            return color

main
    create logo as Logo with "Blue"
    print Logo is {{logo.getColor()}}
```

### Using `class` (Java-like)

```python
class Student
    instance vars:
        * grade as double
    constructor:
        * grade:
    instance methods:
        * getGrade() returns double
            return grade

main
    create student as Student with 85.5
    print Grade: {{student.getGrade()}}
```

## 2. Abstract Synonyms

### Using `abstract` (Technical)

```python
abstract template Animal
    abstract methods:
        * makeSound() returns string

template Dog is-a Animal
    instance methods:
        * makeSound() returns string
            return "Woof!"

main
    create dog as Dog with
    print {{dog.makeSound()}}
```

### Using `contract` (Obligation)

```python
contract template Worker
    must-do methods:
        * work() returns string

template Developer is-a Worker
    instance methods:
        * work() returns string
            return "Writing code"

main
    create dev as Developer with
    print {{dev.work()}}
```

### Using `basic` (Foundation)

```python
basic template Shape
    instance vars:
        * color as string
    constructor:
        * color:
    abstract methods:
        * getArea() returns double

template Circle is-a Shape
    instance vars:
        * radius as double
    constructor:
        * color, radius:
            super(color)
    instance methods:
        * getArea() returns double
            return 3.14 * radius * radius

main
    create circle as Circle with "Red", 5.0
    print Area: {{circle.getArea()}}
```

### Using `base` (Fundamental)

```python
base template Vehicle
    instance vars:
        * speed as int
    constructor:
        * speed:
    abstract methods:
        * move() returns string

template Car is-a Vehicle
    constructor:
        * speed:
            super(speed)
    instance methods:
        * move() returns string
            return "Driving at " + speed + " mph"

main
    create car as Car with 60
    print {{car.move()}}
```

### Using `must-do` (Requirement)

```python
must-do template Employee
    instance vars:
        * name as string
    constructor:
        * name:
    must-do methods:
        * getPaycheck() returns string

template Manager is-a Employee
    constructor:
        * name:
            super(name)
    instance methods:
        * getPaycheck() returns string
            return name + " gets $5000"

main
    create manager as Manager with "Alice"
    print {{manager.getPaycheck()}}
```

## 3. Inheritance Synonyms

### Using `extends` (Technical)

```python
template Animal
    instance vars:
        * name as string
    constructor:
        * name:

template Dog extends Animal
    constructor:
        * name:
            super(name)

main
    create dog as Dog with "Buddy"
    print Dog name: {{dog.name}}
```

### Using `inherits` (Natural)

```python
template Person
    instance vars:
        * age as int
    constructor:
        * age:

template Student inherits Person
    constructor:
        * age:
            super(age)

main
    create student as Student with 20
    print Student age: {{student.age}}
```

### Using `is-a` (Relationship)

```python
template Fruit
    instance vars:
        * color as string
    constructor:
        * color:

template Apple is-a Fruit
    constructor:
        * color:
            super(color)

main
    create apple as Apple with "Red"
    print Apple is {{apple.color}}
```

## 4. Interface Implementation Synonyms

### Using `implements` (Technical)

```python
interface template Flyable
    abstract methods:
        * fly() returns string

template Bird implements Flyable
    instance methods:
        * fly() returns string
            return "Flying high"

main
    create bird as Bird with
    print {{bird.fly()}}
```

### Using `can` (Ability)

```python
interface template Swimmable
    abstract methods:
        * swim() returns string

template Fish can Swimmable
    instance methods:
        * swim() returns string
            return "Swimming fast"

main
    create fish as Fish with
    print {{fish.swim()}}
```

### Using `can-do` (Capability)

```python
interface template Drawable
    abstract methods:
        * draw() returns string

template Circle can-do Drawable
    instance methods:
        * draw() returns string
            return "Drawing a circle"

main
    create circle as Circle with
    print {{circle.draw()}}
```

### Using `capable` (Skilled)

```python
interface template Programmable
    abstract methods:
        * code() returns string

template Robot capable Programmable
    instance methods:
        * code() returns string
            return "Executing program"

main
    create robot as Robot with
    print {{robot.code()}}
```

## 5. Abstract Methods Synonyms

### Using `abstract methods`

```python
abstract template Animal
    abstract methods:
        * makeSound() returns string
        * move() returns string

template Cat is-a Animal
    instance methods:
        * makeSound() returns string
            return "Meow"
        * move() returns string
            return "Prowling"

main
    create cat as Cat with
    print {{cat.makeSound()}} and {{cat.move()}}
```

### Using `must-do methods`

```python
contract template Worker
    must-do methods:
        * work() returns string
        * takeBreak() returns string

template Teacher is-a Worker
    instance methods:
        * work() returns string
            return "Teaching students"
        * takeBreak() returns string
            return "Grading papers"

main
    create teacher as Teacher with
    print {{teacher.work()}}, {{teacher.takeBreak()}}
```

## 6. Constructor Styles

### Original Constructor (Explicit)

```python
template Book
    instance vars:
        * title as string
        * pages as int
    constructor:
        * Book(title):
            this.title = title
            this.pages = 100
        * Book(title, pages):
            this.title = title
            this.pages = pages

main
    create book1 as Book with "Java Guide"
    create book2 as Book with "Python Basics", 200
```

### Simplified Constructor (Auto-assignment)

```python
template Phone
    instance vars:
        * brand as string
        * model as string
    constructor:
        * brand:
            print New phone: {{brand}}
        * brand, model:
            print New {{brand}} {{model}}

main
    create phone1 as Phone with "Apple"
    create phone2 as Phone with "Samsung", "Galaxy"
```

## 7. Static Variables and Methods

### Template/Blueprint/Design/Class Variables & Methods

```python
design Counter
    design vars:
        * totalCount as int with 0
    design methods:
        * getTotal() returns int
            return totalCount
    instance vars:
        * value as int
    constructor:
        * value:
            totalCount++

main
    create c1 as Counter with 10
    create c2 as Counter with 20
    print Total counters: {{Counter.getTotal()}}
```

## 8. Mixed Synonyms Example

```python
basic blueprint Animal
    instance vars:
        * name as string
    constructor:
        * name:
    must-do methods:
        * makeSound() returns string

class Dog inherits Animal can-do Playable
    constructor:
        * name:
            super(name)
    instance methods:
        * makeSound() returns string
            return "Woof!"
        * play() returns string
            return "Fetching ball"

interface design Playable
    abstract methods:
        * play() returns string

main
    create dog as Dog with "Max"
    print {{dog.makeSound()}}
    print {{dog.play()}}
```

## 9. Print Styles

### Simple Print

```python
template Greeter
    instance vars:
        * name as string
    constructor:
        * name:

main
    create greeter as Greeter with "World"
    print Hello {{greeter.name}}!
    print Welcome to PseudoJava
```

### F-string Style Print

```python
template Calculator
    instance vars:
        * result as double
    constructor:
        * result:

main
    create calc as Calculator with 42.5
    print f"The result is {calc.result:.2f}"
```

These examples show all the different synonym combinations in simple, easy-to-understand formats!
