LuaR  

              @ A@   F @   ]  @ ÁŔ   Ć @  Ý   e  Á  AAAĺA   ×Á˙e  Á  ĺÁ  Áĺ ÁĺA Áĺ ß             require        ast_walker        indexed_linked_list 	       ast_util        stack 	       funcstat 
       localfunc        func_proto 
       whilestat        repeatstat        ifstat        PhoB˙                                                    	                                             
                        	           @ ĆŔ  Ý ŔŔŔ Ć A AAÝ  @  @A ÂAGBA B  â  cýĆ B A Ý@      	       func_def        body        new        parent_func_def        ipairs        func_protos        table        remove        error ˘       Unable to find node.func_def in func_protos of parent func_def indicating malformed AST. Every functiondef should be in the func_protos of the parent functiondef        PhoB˙ 	         	      "   !            )       7            	         ,      	               
                        *       @src/optimize/fold_control_statements.lua                                                                                         node               context        	       func_def              (for generator) 	             (for state) 	             (for control) 	             i 
             func_proto 
                _ENV        ill    "    
    @ Ĺ     Ć@   @ Ý@            new_context        parent_func_def        walk_scope E       PhoB˙       
      ,   5   +            "                          *       @src/optimize/fold_control_statements.lua 
                   !   !   !   !   "             parent_func_def     	          scope     	          context    	             ast_walker        on_open %   -    
   
@@
@  A 

@AŔA 
 
@Á
@A  
   
       node_type 	       loopstat        do_jump_back        open_token        repeat_token         close_token        until_token 
       condition E       PhoB˙       
                                                  *       @src/optimize/fold_control_statements.lua 
   &   '   (   (   )   *   *   +   ,   -             node     	          do_jump_back     	       0   ?        F @ @@ ] [   F@    ]   Ŕ     @Ŕ@ Ŕ   @ F A @@ ] [   @
Á
 ÂGB 
@
ŔB
ŔÂ
ŔBGC 
@
ŔB     	       is_falsy 
       condition        get_functiondef        remove_stat        is_const_node 
       node_type 	       loopstat        do_jump_back        open_token        while_token  	       do_token        close_token 
       end_token        PhoB˙                             ,   +      !   +       
               "                                                             *       @src/optimize/fold_control_statements.lua     1   1   1   1   1   2   2   2   3   3   3   3   4   4   4   4   5   5   5   5   5   6   7   8   8   9   :   ;   <   <   =   ?             node        	       func_def                 ast        remove_func_defs_in_scope A   G       F @ @@ ] [    E     Ă  ]@ F@ @@ ] [   Ŕ E     Ă   ]@     	       is_falsy 
       condition        is_const_node m       PhoB˙                                            "                                            *       @src/optimize/fold_control_statements.lua    B   B   B   B   B   C   C   C   C   C   D   D   D   D   D   E   E   E   E   G             node                  ast        convert_repeatstat I   ~    i    Ŕ Ć@@Ŕ Ý    ÁŔ  A   GA GÁAÁ ÇÁ   ŔŔ  AÁA BÇA  AÎŔŔÁ@@AÂ ÇÁ    
A  ÍÁŔ ĄŔ A CBA ÂÂ ÁýC    Ŕ C A
ŔBA ÁÂJĂJÁBÁĂ   ÁĂJÄÄJÁÂJÁÂE JAĹ Ŕ   A@ ÍŔŔîGA GÁŔ[A  GC [   GC JĂĹ   ĹJÄÄJÁBE JÁĹ Ŕ   A FĆ   ]A             get_functiondef        get_top        scope_stack       đ?       ifs 	       is_falsy 
       condition        table        remove        is_const_node       đż 
       elseblock 
       node_type        dostat 	       if_token 	       do_token        value        do        then_token 
       end_token        insert_after_stat        else_token        replace_stat        remove_stat Á      PhoB˙       i      /   ?   7   )                     !                   	   #   -   "   	                            )                     #   &      %   3   7   $         	               %   3   $                           )                  #            %      	                                             )               #                                                    *       @src/optimize/fold_control_statements.lua i   K   K   K   K   K   L   M   M   N   N   O   O   P   P   P   P   P   Q   Q   Q   Q   R   R   R   R   R   S   T   T   U   U   U   U   U   V   V   V   V   V   W   W   W   W   W   X   X   V   Z   Z   Z   [   [   [   [   \   _   _   `   a   b   b   b   c   c   d   d   e   g   h   h   i   i   i   i   j   l   m   o   o   o   o   p   p   p   q   r   s   s   s   t   t   u   u   v   x   x   y   y   y   y   y   {   {   {   ~             node     h          context     h   	       func_def    h          i    h          c    h   
       testblock    L          (for index) #   /          (for limit) $   /          (for step) %   /          j &   .   
       elseblock T   d             _ENV        ast        stack        remove_func_defs_in_scope           F @    Ć@@  D  Ý ]@              walk_scope        new_context =       PhoB˙                )   6   ?   5                          *       @src/optimize/fold_control_statements.lua                                      main                  ast_walker        on_open     *       @src/optimize/fold_control_statements.lua                                            	                     #   %   /   0   0   A   A   I   I            
          ast_walker              ill              ast 	             stack              remove_func_defs_in_scope              delete_func_base_node              on_open              convert_repeatstat              on_open              fold                 _ENV 