(define (domain Depot)
(:requirements :strips :typing)
(:types place locatable - object
	depot distributor - place
        truck hoist surface - locatable
        pallet crate - surface)

(:predicates (at ?x - locatable ?y - place)
             (in ?x - crate ?y - truck)
             (available ?x - hoist)
             (lifting ?x - hoist ?y - crate)
             (clear ?x - surface)
             (on ?x - crate ?y - surface))

(:action Drive
:parameters (?x - truck ?y - place ?z - place) 
:precondition (and (at ?x ?y))
:effect (and (not (at ?x ?y)) (at ?x ?z)))

(:action Load
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (at ?z ?p) (at ?x ?p) (lifting ?x ?y))
:effect (and (in ?y ?z) (not (lifting ?x ?y)) (available ?x)))

(:action Unload 
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (at ?z ?p) (in ?y ?z) (at ?x ?p) (available ?x))
:effect (and (not (in ?y ?z)) (lifting ?x ?y) (not (available ?x))))

(:action Lift
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (at ?x ?p) (available ?x) (at ?y ?p) (clear ?y) (on ?y ?z))
:effect (and (not (available ?x)) (lifting ?x ?y) (not (at ?y ?p)) (not (clear ?y)) (not (on ?y ?z)) (clear ?z)))

(:action Drop 
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (at ?x ?p) (lifting ?x ?y) (at ?z ?p) (clear ?z))
:effect (and (not (lifting ?x ?y)) (available ?x) (at ?y ?p) (clear ?y) (on ?y ?z) (not (clear ?z))))

)