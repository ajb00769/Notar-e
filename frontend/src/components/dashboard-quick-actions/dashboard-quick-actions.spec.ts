import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DashboardQuickActions } from './dashboard-quick-actions';

describe('DashboardQuickActions', () => {
  let component: DashboardQuickActions;
  let fixture: ComponentFixture<DashboardQuickActions>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DashboardQuickActions]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DashboardQuickActions);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
