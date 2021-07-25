# Python packages
import pandas as pd # Generate data frame
import time # Control running time

# Own modules
import main_full_cooperation, main_partial_cooperation, main_residual_cooperation, main_iterative_cooperation, main_no_cooperation

#-----------
# For instances with 5 agents
#--------

instance_list = []
n = 5
for string in ['low','high']:
    for i in range(5):
        instance_list.append('%d_%s_%d' %(n,string,i))

# Data frame to store results
agents_5_df = pd.DataFrame(columns = ['No_cooperation','Full','Full%','Partial', 'Partial%','Residual','Residual%'])
agents_5_time_df = pd.DataFrame(columns = ['No_cooperation','Full','Partial','Residual'])

for instance in instance_list[0:1]:
    time_1 = time.time()
    main_no_cooperation.no_cooperation(instance)
    time_end_no_coop = time.time()
    full_payoff = main_full_cooperation.full_cooperation(instance)
    time_end_full = time.time()
    partial_payoff = main_partial_cooperation.partial_cooperation(instance)
    time_end_partial = time.time() 
    no_cooperation_payoff , residual_payoff = main_residual_cooperation.residual_cooperation(instance)
    time_end_residual = time.time()
    
    temp = [no_cooperation_payoff,full_payoff,(full_payoff-no_cooperation_payoff)/no_cooperation_payoff*100,partial_payoff,
    (partial_payoff-no_cooperation_payoff)/no_cooperation_payoff*100,residual_payoff,(residual_payoff-no_cooperation_payoff)/no_cooperation_payoff*100]
    temp = [round(x,2) for x in temp]

    agents_5_df.loc[instance] = temp

    temp_time = [time_end_no_coop-time_1,time_end_full-time_end_no_coop,time_end_partial-time_end_full,time_end_residual-time_end_partial]
    temp_time = [round(x,2) for x in temp_time]

    agents_5_time_df.loc[instance] = temp_time


file = open("5_agents_payoffs.txt","w")
file.write(agents_5_df.to_latex())
file.close()

file = open("5_agents_times.txt","w")
file.write(agents_5_time_df.to_latex())
file.close()

#------------------------------------------------------------------------
# For instances with 2 agents
#------------------------------------------------------------------------

instance_list = []
n = 2
for string in ['low','high']:
    for i in range(5):
        instance_list.append('%d_%s_%d' %(n,string,i))


#----------------------- PAYOFFS AND RUNNING TIMES -----------------------

# Data frame to store payoffs results
agents_2_df = pd.DataFrame(columns = ['No_cooperation','Full','Full%','Partial', 'Partial%','Residual','Residual%','Iterative','Iterative%'])
# Data frame to store running times
agents_2_time_df = pd.DataFrame(columns = ['No_cooperation','Full','Partial','Residual','Iterative'])

for instance in instance_list[0:1]:
    time_1 = time.time()
    main_no_cooperation.no_cooperation(instance)
    time_end_no_coop = time.time()
    full_payoff = main_full_cooperation.full_cooperation(instance)
    time_end_full = time.time()
    partial_payoff =main_partial_cooperation.partial_cooperation(instance)
    time_end_partial = time.time()
    no_cooperation_payoff , residual_payoff = main_residual_cooperation.residual_cooperation(instance)
    time_end_residual = time.time()
    iterative_payoff, it_for_eq = main_iterative_cooperation.iterative_cooperation(instance)
    time_end_iterative = time.time()

    temp = [no_cooperation_payoff,full_payoff,(full_payoff-no_cooperation_payoff)/no_cooperation_payoff*100,partial_payoff,
    (partial_payoff-no_cooperation_payoff)/no_cooperation_payoff*100,residual_payoff,(residual_payoff-no_cooperation_payoff)/no_cooperation_payoff*100,iterative_payoff,(iterative_payoff-no_cooperation_payoff)/no_cooperation_payoff*100]
    temp = [round(x,2) for x in temp]
    
    agents_2_df.loc[instance] = temp

    temp_time = [time_end_no_coop-time_1,time_end_full-time_end_no_coop,time_end_partial-time_end_full,time_end_residual-time_end_partial,time_end_iterative-time_end_residual]
    temp_time = [round(x,2) for x in temp_time]

    agents_2_time_df.loc[instance] = temp_time


file = open("2_agents_payoffs.txt","w")
file.write(agents_2_df.to_latex())
file.close()

file = open("2_agents_times.txt","w")
file.write(agents_2_time_df.to_latex())
file.close()


# ------------------- ANALYSIS ORDER RELEVANCE FOR ITERATIVE MODEL ---------------------------

# Data frame to compare iterative model with different orders
iter_order_df = pd.DataFrame(columns = ['Order1_payoff','Order2_payoff','Dif%','Order1_it','Order2_it','Dif_it'])

for instance in instance_list[0:1]:
    print(instance)
    iterative_payoff1,it_for_eq1 = main_iterative_cooperation.iterative_cooperation(instance,[0,1])
    iterative_payoff2,it_for_eq2 = main_iterative_cooperation.iterative_cooperation(instance,[1,0])
    temp = [iterative_payoff1,iterative_payoff2,abs(iterative_payoff1-iterative_payoff2)/max(iterative_payoff1,iterative_payoff1)*100,it_for_eq1,it_for_eq2,abs(it_for_eq2-it_for_eq1)]
    iter_order_df.loc[instance] = temp
print(iter_order_df)

file = open("order_comparition.txt","w")
file.write(iter_order_df.to_latex())
file.close()

