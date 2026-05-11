(define (domain snake)
(:requirements :strips :negative-preconditions :equality)
(:constants
    dummypoint
)
(:predicates
    (ispoint ?x)
    (headsnake ?x)
    (spawn ?x)
    (NEXTSPAWN ?x ?y)
    (tailsnake ?x)
    (nextsnake ?x ?y)
    (blocked ?x)
    (ISADJACENT ?x ?y)
)
(:action move-and-eat-no-spawn
    :parameters (?head ?newhead)
    :precondition
    (and
        (headsnake ?head)
        (ispoint ?newhead)
        (not (blocked ?newhead))
        (ISADJACENT ?head ?newhead)
        (spawn dummypoint)
    )
    :effect
    (and
        (not (ispoint ?newhead))
        (headsnake ?newhead)
        (blocked ?newhead)
        (nextsnake ?newhead ?head)
        (not (headsnake ?head))
    )
)

(:action move-and-eat-spawn
    :parameters (?head ?newhead ?spawnpoint ?nextspawnpoint)
    :precondition
    (and
        (headsnake ?head)
        (ispoint ?newhead)
        (not (blocked ?newhead))
        (ISADJACENT ?head ?newhead)
        (spawn ?spawnpoint)
        (NEXTSPAWN ?spawnpoint ?nextspawnpoint)
        (not (= ?spawnpoint dummypoint))
    )
    :effect
    (and
        (not (ispoint ?newhead))
        (headsnake ?newhead)
        (blocked ?newhead)
        (nextsnake ?newhead ?head)
        (not (headsnake ?head))
        (ispoint ?spawnpoint)
        (not (spawn ?spawnpoint))
        (spawn ?nextspawnpoint)
    )
)

(:action move
    :parameters (?head ?newhead ?tail ?newtail)
    :precondition
    (and
        (headsnake ?head)
        (not (ispoint ?newhead))
        (not (blocked ?newhead))
        (ISADJACENT ?head ?newhead)
        (tailsnake ?tail)
        (nextsnake ?newtail ?tail)
    )
    :effect
    (and
        (headsnake ?newhead)
        (blocked ?newhead)
        (nextsnake ?newhead ?head)
        (not (headsnake ?head))
        (not (blocked ?tail))
        (not (tailsnake ?tail))
        (not (nextsnake ?newtail ?tail))
        (tailsnake ?newtail)
    )
)

)