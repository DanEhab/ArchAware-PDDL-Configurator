(define (domain Depot)
(:requirements :strips :typing)
(:types place locatable - object
	depot distributor - place
        truck hoist surface - locatable
        pallet crate - surface)

(:predicates (available ?x - hoist)
             (clear ?x - surface)
             (at ?x - locatable ?y - place)
             (on ?x - crate ?y - surface)
             (in ?x - crate ?y - truck)
             (lifting ?x - hoist ?y - crate))

(:action Drive
:parameters (?x - truck ?y - place ?z - place) 
:precondition (and (at ?x ?y))
:effect (and (not (at ?x ?y)) (at ?x ?z)))

(:action Lift
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (available ?x) (at ?x ?p) (at ?y ?p) (clear ?y) (on ?y ?z))
:effect (and (not (available ?x)) (clear ?z) (not (at ?y ?p)) (not (clear ?y)) (not (on ?y ?z)) (lifting ?x ?y)))

(:action Drop 
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (at ?x ?p) (at ?z ?p) (clear ?z) (lifting ?x ?y))
:effect (and (available ?x) (not (clear ?z)) (at ?y ?p) (clear ?y) (on ?y ?z) (not (lifting ?x ?y))))

(:action Load
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (at ?z ?p) (at ?x ?p) (lifting ?x ?y))
:effect (and (available ?x) (in ?y ?z) (not (lifting ?x ?y))))

(:action Unload 
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (at ?z ?p) (available ?x) (at ?x ?p) (in ?y ?z))
:effect (and (not (available ?x)) (not (in ?y ?z)) (lifting ?x ?y)))

)