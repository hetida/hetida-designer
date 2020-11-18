# hetida designer Backend - Coding Standards

TODO: Add more examples - we'll add those on-the-fly when we find and repair
instances of bad code.

Our most important code style rule is: **Write code for humans.** Make your code
as readable, maintainable and debuggable as possible. Rather than sticking to the
letter of rigid coding standards ask yourself: "What is the solution that provides
most benefit to our users with the lowest total cost of ownership?"

## Table of Contents

* [Java Coding Standard](#Java Coding Standard)
* [Dependency Injection](#dependency-injection)
* [Controllers](#controllers)
* [Serialization](#serialization)
* [Testing](#testing)

## Java Coding Standard

The core of our coding standards are the standard Java [Code Conventions.](https://www.oracle.com/java/technologies/javase/codeconventions-contents.html).

## Dependency Injection

* Use `constructor injection`. Avoid `field injection`.

> Constructor injection makes dependencies explicit and forces you to provide all mandatory dependencies when creating instances of your component.

```java
// bad
public class PersonService {
    @AutoWired
    private PersonRepository personRepositoy;
}

// good
public class PersonService {
    private final PersonRepository personRepository;

    // if the class has only one constructor, @Autowired can be omitted
    public PersonService(PersonRepository personRepository) {
        this.personRepository = personRepository;
    }
}    
```

* Avoid single implementation interfaces.

> A class already exposes an interface: its public members. Adding an identical `interface` definition makes the code harder to navigate and violates [YAGNI](https://en.wikipedia.org/wiki/You_aren%27t_gonna_need_it).
>
> Testing: Earlier mocking frameworks were only capable of mocking interfaces. Recent frameworks like [Mockito](https://site.mockito.org/) can also mock classes. 

```java
// bad
public interface PersonService {
    List<Person> getPersons();
}

public class PersonServiceImpl implements PersonService {
    public List<Person> getPersons() {
        // more code
    }
}

// good
public class PersonService {
    public List<Person> getPersons() {
        // more code
    }
}
```

**[⬆ back to top](#table-of-contents)**

## Controllers

* Use `@RestController` when providing a RESTful API.

```java
// bad
@Controller
public class PersonController {
    @ResponseBody
    @GetMapping("/persons/{id}")
    public Person show(@PathVariable long id) {
        // more code
    }
}

// good
@RestController
public class PersonController {
    @GetMapping("/persons/{id}")
    public Person show(@PathVariable long id) {
        // more code
    }
}
```

* Use `@GetMapping`, `@PostMapping` etc. instead of `@RequestMapping`.

```java
// bad
@RestController
public class PersonController {
    @RequestMapping(method = RequestMethod.GET, value = "/persons/{id}")
    public Person show(@PathVariable long id) {
        // more code
    }
}

// good
@RestController
public class PersonController {
    @GetMapping("/persons/{id}")
    public Person show(@PathVariable long id) {
        // more code
    }
}
```

**[⬆ back to top](#table-of-contents)**

## Serialization

* Do not map your JSON objects to `JavaBeans`.

> JavaBeans are mutable and split object construction across multiple calls.

```java
// bad
public class Person {
    private String firstname;
    private String lastname;

    public void setFirstname() {
        this.firstname = firstname;
    }

    public String getFirstname() {
        return firstname;
    }

    public void setLastname() {
        this.lastname = lastname;
    }

    public String getLastname() {
        return lastname;
    }
}

// good
public class Person {
    private final String firstname;
    private final String lastname;

    // requires your code to be compiled with a Java 8 compliant compiler 
    // with the -parameter flag turned on
    // as of Spring Boot 2.0 or higher, this is the default
    @JsonCreator
    public Person(String firstname, String lastname) {
        this.firstname = firstname;
        this.lastname = lastname;
    }

    public String getFirstname() {
        return firstname;
    }

    public String getLastname() {
        return lastname;
    }
}

// best
public class Person {
    private final String firstname;
    private final String lastname;

    // if the class has a only one constructor, @JsonCreator can be omitted
    public Person(String firstname, String lastname) {
        this.firstname = firstname;
        this.lastname = lastname;
    }

    public String getFirstname() {
        return firstname;
    }

    public String getLastname() {
        return lastname;
    }
}
```

**[⬆ back to top](#table-of-contents)**

## Testing

* Keep Spring out of your unit tests.

```java
class PersonServiceTests {
    @Test
    void testGetPersons() {
        // given
        PersonRepository personRepository = mock(PersonRepository.class);
        when(personRepository.findAll()).thenReturn(List.of(new Person("Max", "Mustermann")));

        PersonService personService = new PersonService(personRepository);

        // when
        List<Person> persons = personService.getPersons();

        // then
        assertThat(persons).extracting(Person::getFirstname, Person::getLastname).containsExactly("Max", "Mustermann");
    }
}
```

* Use [AssertJ](http://joel-costigliola.github.io/assertj/). Avoid [Hamcrest](http://hamcrest.org/).

> `AssertJ` is more actively developed, requires only one static import, and allows you to discover assertions through autocompletion.

```java
// bad
import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.is;
import static org.hamcrest.Matchers.not;
import static org.hamcrest.Matchers.empty;

assertThat(persons), is(not(empty())));

// good
import static org.assertj.core.api.Assertions.assertThat;

assertThat(persons).isNotEmpty();
```

**[⬆ back to top](#table-of-contents)**
